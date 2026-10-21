# -*- coding: utf-8 -*-
"""apply_copy_menus.py - round CP-2, 21 Oct 2026.

THREE FEATURES WERE REACHABLE ONLY ON A PHONE.

Demetri, 21 October:

    "I don't see Copy this week nor save this week as a menu???"

HE COULD NOT. MW-1 put Copy this week to..., Save this week as a Menu
and Apply a Menu INSIDE the More menu on 19 October, and gave none of
them a button in the bar. base hides that menu above 768px:

    .action-more-wrapper { display: none; }          <- no media query
    @media screen and (max-width: 768px) {
      .action-more-wrapper { display: block; ... }
    }

Measured at four widths: the More button is display:none at 1900,
1280 and 900, and block at 390. The menu is a PHONE control. It
exists to catch secondaries that base hid on a narrow screen - which
is why its items are supposed to be COPIES of bar controls. On 32
bars in this application, 31 use it exactly that way.

So for two days three features existed only on his phone, on the one
screen he does not plan meals on.

THE SHAPE OF THE FIX IS HIS, taken after the options were measured
rather than argued: "Option A - as you recommend."

    Copy...          a range onto a landing date
    Saved Menus...   save one, apply one, delete one - all three

TWO SECONDARIES, NOT THREE AND NOT A DROPDOWN. 119 bars in this
application carry a median of 2 controls and 19 carry four or more;
the largest carries eight. Bar space was never the constraint. And
the only dropdown-in-a-bar that exists here is the More menu itself,
which is the thing that caused this - inventing a second one would
have been building the bug again in a new colour.

COPY IS ONE CONTROL, NOT FOUR. He asked for day, week, month and an
arbitrary range. copy_week_rows already copies by DATE OFFSET -
`(entry.date - src_start).days` onto `dst_start + offset` - so it has
always been able to do any span; only the door was week-shaped. The
new view hands it a range. Day, This week and This month are presets
that fill the two dates in, not four code paths.

AND THE LEFTOVERS STILL FOLLOW THEIR PARENTS, because that is the
engine's job and the engine is untouched: a leftover whose parent is
not in the copied span is dropped, or the shopping list would charge
the new dates for a meal in the old ones.

Idempotent. Every file backed up to .bak_copymenus.
"""
import os
import re
import sys

SUFFIX = '.bak_copymenus'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
ME = 'test_copy_menus.py'
PATCHER = 'apply_copy_menus.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
HELP = os.path.join('pages', 'help_content', 'administration.html')
MARK = 'CP-2, 21 Oct 2026'
CHECK = False
CREATES = ()

# =====================================================================
# THE VIEW - a range onto a landing date
# =====================================================================
VIEW_WAS = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def save_menu(request):"""

VIEW_NOW = '''@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def copy_meal_range(request):
    """Copy every meal in a span of days onto another span, keeping
    the original.

    CP-2, 21 Oct 2026. Demetri asked for four things - a day onto a
    day, a week onto a week, a month onto a month, and any range onto
    a start date - and they are one thing. copy_week_rows has always
    copied by DATE OFFSET rather than by weekday:

        offset = (entry.date - src_start).days
        when   = dst_start + timedelta(days=offset)

    so the span it can carry was never a week; only the door was
    week-shaped. Day, This week and This month are presets in the
    dialog that fill in two dates. There is one code path.

    ADDS ALONGSIDE, which is the 19 October decision, and the engine
    lands each copy AFTER whatever the destination day already holds.

    A LEFTOVER WHOSE PARENT IS NOT IN THE SPAN IS DROPPED - also the
    engine's doing, and the reason this view does not filter the rows
    itself. A leftover of nothing buys nothing and says nothing.
    """
    start = week_of(request.POST.get('from'), None)
    end = week_of(request.POST.get('to'), None)
    onto = week_of(request.POST.get('onto'), None)
    back = planner_back(request, onto or start or timezone.now().date())

    if start is None or end is None or onto is None:
        messages.error(request, 'Those dates could not be read.')
        return redirect(back)
    if end < start:
        start, end = end, start

    # THE SHOPPING LIST'S CEILING, deliberately the same number. Three
    # pages now take a span and a fourth limit would be the one that
    # surprises somebody.
    if (end - start).days > 92:
        messages.error(request, 'A copy covers at most 13 weeks.')
        return redirect(back)

    # COPYING ONTO ITSELF IS NOT A COPY. Landing on the first day of
    # the span you are copying would duplicate every meal in place.
    if start <= onto <= end:
        messages.error(request, 'That would copy the days onto '
                                'themselves. Pick a date outside '
                                '%s to %s.'
                       % (day_label(start), day_label(end)))
        return redirect(back)

    rows = list(MealEntry.objects
                .filter(date__gte=start, date__lte=end)
                .select_related('recipe', 'leftover_of')
                .order_by('date', 'sort_order'))
    if not rows:
        messages.error(request, 'There is nothing on %s to %s to copy.'
                       % (day_label(start), day_label(end)))
        return redirect(back)

    made = copy_week_rows(rows, start, onto, request.user)
    span = (end - start).days + 1
    messages.success(
        request,
        'Copied %d meal%s from %d day%s onto %s.'
        % (made, '' if made == 1 else 's',
           span, '' if span == 1 else 's', day_label(onto)))
    return redirect(planner_back(request, onto))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def save_menu(request):'''

# =====================================================================
# "SAY SO FIRST" - the half of the collision decision that was week-shaped
# =====================================================================
# MW-1's dialog asked the server what the TARGET WEEK already held and
# would not let Copy be pressed until the answer came back. That is not
# decoration: the standing decision is "add alongside, AND SAY SO
# FIRST", and the first draft of this round quietly dropped the second
# half by replacing the week dialog with a range one.
#
# test_meal_week caught it. The preview endpoint takes a range now -
# ?from= and ?to= - and ?week= still answers, because copy_meal_week
# is untouched and still uses it.
PREVIEW_WAS = """    week = week_of(request.GET.get('week'), None)
    if week is None:
        return JsonResponse({'success': False,
                             'error': 'That week could not be read.'},
                            status=400)"""

PREVIEW_NOW = '''    # A SPAN, NOT ONLY A WEEK - CP-2, 21 Oct 2026. The copy dialog
    # takes any range now, so the question it has to ask is "what is
    # already on these days", not "what is already on this week".
    # ?week= still answers below: copy_meal_week is untouched.
    first = week_of(request.GET.get('from'), None)
    last = week_of(request.GET.get('to'), None)
    if first is not None and last is not None:
        if last < first:
            first, last = last, first
        if (last - first).days > 92:
            return JsonResponse({'success': False,
                                 'error': 'A copy covers at most '
                                          '13 weeks.'}, status=400)
        span = list(MealEntry.objects
                    .filter(date__gte=first, date__lte=last)
                    .only('date'))
        return JsonResponse({
            'success': True,
            'week': first.strftime('%Y-%m-%d'),
            'label': day_label(first) if first == last
                     else '%s - %s' % (day_label(first), day_label(last)),
            'meals': len(span),
            'days_with_meals': len({e.date for e in span}),
        })

    week = week_of(request.GET.get('week'), None)
    if week is None:
        return JsonResponse({'success': False,
                             'error': 'That week could not be read.'},
                            status=400)'''


# =====================================================================
# THE JAVASCRIPT MW-1 WROTE FOR THE THREE DIALOGS
# =====================================================================
# resetCopyWeek, resetSaveMenu, resetApplyMenu and copyPreview all
# address elements inside dialogs this round deletes. Left behind they
# are not merely dead: test_req_marker reads every getElementById on
# every page and reports a selector the markup never provides, which
# is how a handler that will throw at runtime gets found before a user
# finds it. pickMenu and deleteMenu stay - the menus dialog still has
# a list and a trashcan.
DEAD_JS_AT = """// ------------------------------------------------------- the week moves
// MW-1, 19 Oct 2026. Three dialogs: copy a week, save a week as a
// Menu, apply a Menu. Each is emptied as it opens - C19's lesson, and
// the picker above does the same thing for the same reason."""

DEAD_JS_END = "function pickMenu(el) {"

DEAD_JS_NOW = """// ------------------------------------------------------- the week moves
// MW-1, 19 Oct 2026, cut back by CP-2 on 21 Oct 2026.
//
// resetCopyWeek, resetSaveMenu, resetApplyMenu and copyPreview all
// addressed elements inside the three dialogs this round replaced.
// Left behind they would not merely be dead: test_req_marker reads
// every getElementById on every page and reports a selector the
// markup never provides, which is how a handler that will throw at
// runtime is found before a user finds it.
//
// The copy dialog's own script - presets, seeding and the preview
// that says what the landing days already hold - is a block of its
// own at the end of this file, below base's jQuery.

"""


URL_WAS = """    path('meal_plans/copy_week/', views.copy_meal_week, name='copy_meal_week'),"""
URL_NOW = """    path('meal_plans/copy_week/', views.copy_meal_week, name='copy_meal_week'),
    # CP-2, 21 Oct 2026 - any span of days onto a landing date. The
    # week endpoint above is left alone; its preview is week-shaped.
    path('meal_plans/copy_range/', views.copy_meal_range,
         name='copy_meal_range'),"""


# =====================================================================
# THE BAR - two secondaries where there were none
# =====================================================================
BAR_WAS = """        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#meal_plansHelpModal">
            <i class="fas fa-question-circle"></i> Help
        </button>"""

BAR_NOW = """        {% if perms.auth.can_edit_recipes %}
        {# BACK ON THE BAR - CP-2, 21 Oct 2026.                       #}
        {#                                                            #}
        {# MW-1 put Copy, Save-as-Menu and Apply-a-Menu inside the    #}
        {# More menu and gave none of them a bar button. base hides   #}
        {# that menu above 768px - it is a PHONE control, there to    #}
        {# catch secondaries a narrow screen hid - so for two days    #}
        {# three features existed only on a phone. Demetri: "I don't  #}
        {# see Copy this week nor save this week as a menu???"        #}
        {#                                                            #}
        {# TWO, because Copy is about dates and a Menu is a saved set #}
        {# of meals: Save-as and Apply are two halves of one idea and #}
        {# live in one dialog, which also gives Delete a home - it    #}
        {# was a trashcan buried inside Apply.                        #}
        <button type="button" class="btn action-secondary"
                data-toggle="modal" data-target="#copyRangeModal">
            <i class="fas fa-copy"></i> Copy&hellip;
        </button>
        <button type="button" class="btn action-secondary"
                data-toggle="modal" data-target="#menusModal">
            <i class="fas fa-bookmark"></i> Saved Menus&hellip;
        </button>
        {% endif %}
        <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#meal_plansHelpModal">
            <i class="fas fa-question-circle"></i> Help
        </button>"""


# =====================================================================
# THE MORE MENU - the three go, two twins arrive
# =====================================================================
MENU_WAS = """                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetCopyWeek()"
                        data-toggle="modal" data-target="#copyWeekModal">
                    <i class="fas fa-copy"></i> Copy this week to...
                </button>
                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetSaveMenu()"
                        data-toggle="modal" data-target="#saveMenuModal">
                    <i class="fas fa-bookmark"></i> Save this week as a Menu
                </button>
                <button type="button" class="action-more-item" role="menuitem"
                        onclick="resetApplyMenu()"
                        data-toggle="modal" data-target="#applyMenuModal">
                    <i class="fas fa-list-ul"></i> Apply a Menu...
                </button>"""

MENU_NOW = """                {# TWINS, NOT HOMES - CP-2, 21 Oct 2026.                  #}
                {#                                                        #}
                {# These three were the only copies in the application    #}
                {# of a feature that had no bar button, and this menu is  #}
                {# display:none above 768px - so they could be reached    #}
                {# only on a phone. They are bar secondaries now, and     #}
                {# what sits here is what sits in every other menu in     #}
                {# the tree: a twin of a control that exists outside it.  #}
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#copyRangeModal">
                    <i class="fas fa-copy"></i> Copy...
                </button>
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#menusModal">
                    <i class="fas fa-bookmark"></i> Saved Menus...
                </button>"""


# =====================================================================
# THE GUIDE
# =====================================================================
# MH-3's whole point is that the guide and the screen are checked
# against each other, and test_meal_guide3 asks both sides of every
# sentence. A tab describing three controls nobody can find would be
# worse than a tab that said nothing.
HELP_INTRO_WAS = """    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Three controls, and all three sit behind the <strong><i class="fas fa-ellipsis-v"></i></strong> button on the planner's own bar &mdash; beside Shopping List and Help. They act on <strong>the week on screen</strong>, so pick the week first.</p>"""

HELP_INTRO_NOW = """    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Two buttons on the planner's own bar &mdash; <strong>Copy&hellip;</strong> and <strong>Saved Menus&hellip;</strong> &mdash; beside Shopping List and Print. On a phone they move into the <strong><i class="fas fa-ellipsis-v"></i></strong> menu, which is where a narrow screen puts every secondary.</p>"""

HELP_CARDS_WAS = """      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-copy" style="color:#28a745;"></i> Copy this week to&hellip;</strong> Pick any day in the week you want and every meal on screen lands on the matching weekday of that week, with the servings it was cooked for. Nothing stays linked afterwards &mdash; change the new week and the old one does not move.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-bookmark" style="color:#0e7c8b;"></i> Save this week as a Menu.</strong> Give the week a name and it is kept <strong>by weekday</strong> rather than by date. That is the difference between a Menu and a copy: a week you save in October can be applied to a week in December, because what is stored is &ldquo;Monday, Thursday, Sunday&rdquo; and not three dates in October.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list-ul" style="color:#0e7c8b;"></i> Apply a Menu&hellip;</strong> Choose one from the list and its meals are added to the week on screen. The menu itself is unchanged &mdash; applying it is a stamp, not a move, so the same menu can be used every month. Each row says how many meals it holds, and carries a <strong>trashcan</strong> to forget it.
      </div>"""

HELP_CARDS_NOW = """      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-copy" style="color:#28a745;"></i> Copy meals to another date.</strong> Any stretch of days, not just a week. <strong>This day</strong>, <strong>This week</strong> and <strong>This month</strong> fill the two dates in for you, or type them yourself &mdash; a long weekend, ten days, a fortnight. Every meal in that stretch lands on the matching day of the new dates, with the servings it was cooked for, and the originals stay exactly where they are. Nothing is linked afterwards: change the copy and the first one does not move.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-bookmark" style="color:#0e7c8b;"></i> Saved Menus.</strong> One dialog, three things. <strong>Save this week</strong> keeps the week on screen under a name &mdash; <strong>by weekday</strong> rather than by date, which is the difference between a Menu and a copy: a week saved in October can be applied to a week in December, because what is stored is &ldquo;Monday, Thursday, Sunday&rdquo; and not three dates in October. <strong>Your menus</strong> lists what you have saved and adds the one you pick to the week on screen &mdash; a stamp, not a move, so the same menu can be used every month. Each row says how many meals it holds and carries a <strong>trashcan</strong> to forget it.
      </div>"""

HELP_COUNT_WAS = """<strong style="color:#2c3e50;"><i class="fas fa-layer-group" style="color:#e6a817;"></i> Two meals landing on one day gives you two meals.</strong> Nothing is replaced and nothing is skipped. Before <strong>Copy the Week</strong> can be pressed, the dialog counts what the target week already holds and tells you &mdash; so a day that ends up with two dinners is something you chose and can see, rather than something that happened quietly."""

HELP_COUNT_NOW = """<strong style="color:#2c3e50;"><i class="fas fa-layer-group" style="color:#e6a817;"></i> Two meals landing on one day gives you two meals.</strong> Nothing is replaced and nothing is skipped. Before <strong>Copy</strong> can be pressed, the dialog counts what the target days already hold and tells you &mdash; so a day that ends up with two dinners is something you chose and can see, rather than something that happened quietly."""

HELP_TIP_WAS = """That is what a Menu is for; <strong>Copy this week to&hellip;</strong> is for last week."""

HELP_TIP_NOW = """That is what a Menu is for; <strong>Copy&hellip;</strong> is for last week - or any stretch of days, onto any date."""

HELP_PERMS_WAS = """      <i class="fas fa-user-lock"></i> <strong>You need editing rights.</strong> A reader can see the week and shop from it, but the <strong><i class="fas fa-ellipsis-v"></i></strong> button is not there without permission to edit recipes."""

HELP_PERMS_NOW = """      <i class="fas fa-user-lock"></i> <strong>You need editing rights.</strong> A reader can see the week and shop from it, but <strong>Copy&hellip;</strong> and <strong>Saved Menus&hellip;</strong> are not there without permission to edit recipes."""


# =====================================================================
# THE PINS OTHER ROUNDS LEFT, MOVED HERE
# =====================================================================
# Every one of these was found by the 21 October sweep and every one
# is a number or a name that this round really changed. A round that
# changes a shape has to move the pin that measures the shape, in the
# same patcher, or the next sweep reports today's decision as a
# regression.
PINS = (
    # ---- MW-1's own suite: the dialogs, the controls, the preview
    ('test_meal_week.py',
     "DIALOGS = ('copyWeekModal', 'saveMenuModal', 'applyMenuModal')",
     "# CP-2, 21 Oct 2026 - TWO, not three. The three were reachable\n"
     "# only on a phone: base hides .action-more-wrapper above 768px,\n"
     "# so a feature whose only control lives in that menu cannot be\n"
     "# used on a desktop at all. Demetri: \"I don't see Copy this week\n"
     "# nor save this week as a menu???\"\n"
     "#\n"
     "# Save-as and Apply are two halves of one idea - a named set of\n"
     "# meals kept by weekday - and live in one dialog now, which also\n"
     "# gives Delete a home instead of a trashcan buried inside Apply.\n"
     "DIALOGS = ('copyRangeModal', 'menusModal')",
     'the dialogs'),
    ('test_meal_week.py',
     """    c['the three controls live in base\\'s More menu'] = (
        tcode.count('id="actionMoreBtn"') == 1
        and tcode.count('data-menu-panel') == 1)""",
     """    # CP-2, 21 Oct 2026 - THE BAR, AND THE MENU AS A TWIN. The menu
    # is a phone control: base hides it above 768px. A feature whose
    # only control lives there is a feature nobody can reach on a
    # desktop, which is what these two were for two days.
    c['the two controls live on the bar'] = (
        tcode.count('id="actionMoreBtn"') == 1
        and tcode.count('data-menu-panel') == 1
        and all('data-target="#%s"' % m in
                tcode[tcode.index('page-action-buttons'):
                      tcode.index('action-more-menu')]
                for m in DIALOGS))""",
     'the controls'),
    ('test_meal_week.py',
     """    for mid in DIALOGS:
        c['  one control targets %s' % mid] = (
            tcode.count('data-target="#%s"' % mid) == 1)""",
     """    # TWO EACH, AND THAT IS THE POINT - CP-2, 21 Oct 2026. One in
    # the bar for a desktop and one in the More menu for a phone,
    # because base hides each of those at the other's width. Exactly
    # one is reachable at a time; test_copy_menus measures that over
    # all 32 bars in the application, in both directions.
    for mid in DIALOGS:
        c['  two controls target %s - bar and menu' % mid] = (
            len(re.findall(r'<(?:button|a)\\b[^>]*data-target="#%s"' % mid,
                           tcode)) == 2)""",
     'the twins'),
    ('test_meal_week.py',
     """    c['the Apply dialog says where menus come from when there are none'] = (
        'Save this week as a Menu</strong>' in tcode)""",
     """    # CP-2, 21 Oct 2026 - the empty state can point UP now rather
    # than at a dialog the reader cannot see from here: Save and
    # Apply are two sections of one dialog, so "Save this week" is
    # eighty pixels above the sentence that names it.
    c['the Apply dialog says where menus come from when there are none'] = (
        'Save this week</strong> above' in tcode)""",
     'the empty state'),
    ('test_meal_week.py',
     """for text in ('id="copyWeekModal"', 'id="saveMenuModal"',
             'id="applyMenuModal"', 'added alongside',
             'def copy_week_rows(', "name='meal_week_preview'"):""",
     """# CP-2, 21 Oct 2026 - the two dialogs that replaced the three. A
# sentinel pointed at a string a round renamed stops the push BEFORE
# any suite runs, and twenty-two suites in this tree check that every
# sentinel still resolves - so three stale ones turned one change
# into twenty-two red suites in the 21 October sweep.
for text in ('id="copyRangeModal"', 'id="menusModal"',
             'added alongside',
             'def copy_week_rows(', "name='meal_week_preview'"):""",
     'the pre-flight'),
    ('test_meal_week.py',
     """    c['  and the Copy button starts DISABLED'] = (
        'id="copyWeekGo" disabled' in tcode)""",
     """    # CP-2, 21 Oct 2026 - renamed with the dialog, and the question
    # it asks is a RANGE now rather than a week. The decision it
    # serves is unchanged and is the reason this claim exists: "add
    # alongside, AND SAY SO FIRST".
    c['  and the Copy button starts DISABLED'] = (
        'id="cpGo" disabled' in tcode)""",
     'the disabled button'),
    ('test_meal_week.py',
     """    c['the delete form is OUTSIDE the apply form'] = (
        tcode.find('id="deleteMenuForm"') > tcode.find('id="applyMenuModal"')
        and '</form>' in tcode[tcode.find('id="applyMenuModal"'):
                               tcode.find('id="deleteMenuForm"')])""",
     """    # CP-2, 21 Oct 2026 - the apply form is inside menusModal now,
    # and the delete form is still its own top-level <form hidden>.
    # The claim is unchanged in substance: a form cannot nest, and a
    # delete nested inside apply would submit the wrong action.
    c['the delete form is OUTSIDE the apply form'] = (
        tcode.find('id="deleteMenuForm"') > tcode.find('id="menusModal"')
        and '</form>' in tcode[tcode.find('id="menusModal"'):
                               tcode.find('id="deleteMenuForm"')])""",
     'the delete form'),

    # ---- MH-3's guide suite, both sides of every sentence
    ('test_meal_guide3.py',
     """    for phrase in ('Copy this week to', 'Save this week as a Menu',
                   'Apply a Menu'):
        c['  it names %r' % phrase] = phrase in w
    c['  and says where the three live'] = 'fa-ellipsis-v' in w""",
     """    # CP-2, 21 Oct 2026 - the two the planner really has. The three
    # it named were in a menu base hides above 768px.
    for phrase in ('Copy meals to another date', 'Saved Menus'):
        c['  it names %r' % phrase] = phrase in w
    c['  and says where the two live, and where a phone puts them'] = (
        'fa-ellipsis-v' in w and 'bar' in w)""",
     'the phrases'),
    ('test_meal_guide3.py',
     """    for mid, phrase in (('copyWeekModal', 'Copy this week to'),
                        ('saveMenuModal', 'Save this week as a Menu'),
                        ('applyMenuModal', 'Apply a Menu'),""",
     """    for mid, phrase in (('copyRangeModal', 'Copy meals to another date'),
                        ('menusModal', 'Saved Menus'),""",
     'the controls'),

    # ---- MH-2/MH-5's help suite, the same two places
    ('test_meal_help.py',
     """    for text, what in (("id=\\"copyWeekModal\\"", 'Copy this week to'),
                       ("id=\\"saveMenuModal\\"", 'Save this week as a Menu'),
                       ("id=\\"applyMenuModal\\"", 'Apply a Menu'),""",
     """    # CP-2, 21 Oct 2026 - the two dialogs that replaced the
    # three. They were reachable only on a phone: base hides the
    # More menu above 768px and nothing else pointed at them.
    for text, what in (("id=\\"copyRangeModal\\"",
                        'Copy meals to another date'),
                       ("id=\\"menusModal\\"", 'Saved Menus'),""",
     'the controls'),
    ('test_meal_help.py',
     """    for phrase in ('Copy this week to', 'Save this week as a Menu',
                   'Apply a Menu', 'Add Note', 'Leftovers'):""",
     """    for phrase in ('Copy meals to another date', 'Saved Menus',
                   'Add Note', 'Leftovers'):""",
     'the phrases'),

    # ---- BO-1, this morning: the bar it reordered has two more on it
    ('test_bar_first.py',
     "    c['THE BAR READS PSSB - the finding'] = (seq == 'PSSB')",
     "    # CP-2, 21 Oct 2026 - PSSSSB. BO-1 reordered four controls\n"
     "    # into PSSB; CP-2 added Copy... and Saved Menus... as two\n"
     "    # more secondaries the same day. House order and the primary\n"
     "    # first - the whole of what BO-1 claimed - are unchanged, and\n"
     "    # section 3 still reads the order off the rendered page.\n"
     "    c['THE BAR READS PSSSSB - the finding'] = (seq == 'PSSSSB')",
     'the sequence'),
    ('test_bar_first.py',
     """ok(sorted(oldseq) == sorted(roles_in(T.code_only(bar_of(NOW[TPL])))),
   'and the bar holds the same controls it held, reordered',
   '%r -> %r' % (oldseq, roles_in(T.code_only(bar_of(NOW[TPL])))))""",
     """# CP-2, 21 Oct 2026 - NOTHING LEFT. The claim was equality, which
# a later round that ADDS a control breaks without taking anything
# away. What BO-1 asserts is that its reorder dropped nothing, so
# every role it had is still there at least as often, and the one
# primary is still exactly one.
_seqnow = roles_in(T.code_only(bar_of(NOW[TPL])))
ok(all(_seqnow.count(r) >= oldseq.count(r) for r in set(oldseq))
   and _seqnow.count('P') == oldseq.count('P')
   and _seqnow.count('B') == oldseq.count('B'),
   'and nothing BO-1 moved left the bar - CP-2 added two secondaries '
   'to it later the same day',
   '%r -> %r' % (oldseq, _seqnow))""",
     'the controls kept'),

    # ---- PB-2's suite: one more view returns through the helper
    ('test_planner_back.py',
     'N_REDIRECTS = 16',
     'N_REDIRECTS = 18   # CP-2, 21 Oct 2026 - copy_meal_range asks '
     'the helper twice: once for the address every refusal returns to, '
     'and once for the one a successful copy returns to, which is the '
     'LANDING date rather than the day you started on.   # (was 16)',
     'the redirects'),

    # ---- MH-5's suite, this morning: it measures every help tab and
    # holds the ones its own round did not touch to the pixel. This
    # round rewrites mp-week - three controls become two - and
    # mp-tips names Copy in a sentence, so both move.
    ('test_meal_guide5.py',
     """                        if slug in ('mp-calendar', 'mp-build',
                                    'mp-shopping', 'mp-tips'):""",
     """                        # CP-2, 21 Oct 2026 - mp-week joins them.
                        # Three controls became two and the tab is
                        # 601 -> 598px on a desktop, 1128 -> 1105 on
                        # a phone. A tab that describes controls
                        # nobody can find would have kept its height
                        # exactly.
                        if slug in ('mp-calendar', 'mp-build',
                                    'mp-shopping', 'mp-tips',
                                    'mp-week'):""",
     'the tab heights'),

    # ---- PN-2's suite: three dialog footers out, two in
    ('test_drift_root.py',
     'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 90, 89   # RD-1 and RD-2',
     'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88   # CP-2, 21 Oct '
     '2026 - three dialogs leave the planner and two arrive, so one '
     '.modal-footer wrapper goes. BOTH matchers fall by the same one, '
     'which is what an ordinary wrapper does and is the point of '
     'keeping the pair.   # (was 90, 89)   # RD-1 and RD-2',
     'the footers'),
)


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
    raise SystemExit('CP-2 REFUSED: %s' % msg)


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


def cut(text, open_at, before, new, where):
    """Replace everything from `open_at` up to `before` with `new`.

    Both ends unique, and the end is the thing that must SURVIVE -
    so a region that has grown still ends where it ended, and a
    region that has moved refuses rather than eating its neighbour.
    """
    once(text, open_at, where)
    once(text, before, where)
    i = text.index(fit(text, open_at))
    j = text.index(fit(text, before))
    if j <= i:
        refuse('%s: the region closes before it opens' % where)
    return text[:i] + fit(text, new) + text[j:]


def modal(text, mid):
    """One <div class="modal ..." id="mid"> ... </div>, brace-counted."""
    i = text.index('id="%s"' % mid)
    i = text.rindex('<div class="modal', 0, i)
    d, j = 0, i
    while True:
        a = text.find('<div', j)
        b = text.find('</div>', j)
        if b < 0:
            refuse('%s: the %s dialog does not close' % (TPL, mid))
        if 0 <= a < b:
            d += 1
            j = a + 4
        else:
            d -= 1
            j = b + 6
            if d == 0:
                return i, j


# =====================================================================
# THE COPY DIALOG - one control, three presets
# =====================================================================
COPY_MODAL = '''{# ===================================================== copy... #}
{# ONE DIALOG FOR FOUR THINGS - CP-2, 21 Oct 2026. He asked for a   #}
{# day, a week, a month and an arbitrary range onto a start date.   #}
{# copy_week_rows copies by DATE OFFSET, so all four are one call;  #}
{# the three buttons below fill in two dates and nothing else.      #}
<div class="modal fade" id="copyRangeModal" tabindex="-1" role="dialog"
     aria-labelledby="copyRangeLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="copyRangeLabel">
                    <i class="fas fa-copy"></i> Copy meals to another date
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <form method="POST" action="{% url 'copy_meal_range' %}">
                {% csrf_token %}
                {# THE VIEW AND THE DAY TRAVEL WITH IT - PB-2 and PB-3. #}
                <input type="hidden" name="view" value="{{ view_mode }}">
                <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">
                <div class="modal-body">
                    <p class="text-muted" style="font-size:13px;">
                        The meals stay where they are. A copy of each one
                        lands on the matching day of the new dates,
                        alongside anything already there.
                    </p>
                    <div class="form-group">
                        <label><strong>Copy</strong></label>
                        <div class="cp-presets">
                            <button type="button" class="btn action-secondary cp-preset"
                                    data-cp-span="day">This day</button>
                            <button type="button" class="btn action-secondary cp-preset"
                                    data-cp-span="week">This week</button>
                            <button type="button" class="btn action-secondary cp-preset"
                                    data-cp-span="month">This month</button>
                        </div>
                    </div>
                    <div class="cp-dates">
                        <div class="form-group">
                            <label for="cpFrom"><strong>From</strong></label>
                            <input type="date" class="form-control" id="cpFrom"
                                   name="from" required>
                        </div>
                        <div class="form-group">
                            <label for="cpTo"><strong>To</strong></label>
                            <input type="date" class="form-control" id="cpTo"
                                   name="to" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="cpOnto"><strong>Landing on</strong></label>
                        <input type="date" class="form-control" id="cpOnto"
                               name="onto" required>
                        <small class="form-text text-muted">
                            The first day of the copy. A span of seven days
                            landing on a Monday fills that Monday to Sunday.
                        </small>
                    </div>
                    {# SAY SO FIRST - the other half of the 19 October  #}
                    {# collision decision, and the half the first draft #}
                    {# of this round quietly dropped. Before Copy can   #}
                    {# be pressed the dialog asks the server what the   #}
                    {# landing days already hold and says it. The       #}
                    {# button is enabled by the ANSWER, not by a date   #}
                    {# being typed: a copy that went ahead while the    #}
                    {# count was still in flight would be the quieter   #}
                    {# conscience the decision was taken to avoid.      #}
                    <div id="cpNote"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn action-primary" id="cpGo" disabled>
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

'''

COPY_JS = '''
{# THE PRESETS - CP-2, 21 Oct 2026. Three buttons that fill two     #}
{# date fields. No fourth code path, on the page or in the view.    #}
{# A BLOCK OF ITS OWN, like RD-1's shell and AP-1's popover: in the #}
{# page's shared script it would sit downstream of everything above #}
{# it, and anything that throws up there takes this with it.        #}
<script>
(function () {
    var ANCHOR = '{{ anchor|date:"Y-m-d" }}';
    var WEEK_FROM = '{{ week_start|date:"Y-m-d" }}';
    var WEEK_TO = '{{ week_end|date:"Y-m-d" }}';
    var PREVIEW = '{% url "meal_week_preview" %}';

    function el(id) { return document.getElementById(id); }

    function iso(d) {
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    function span(kind) {
        if (kind === 'day') { return [ANCHOR, ANCHOR]; }
        if (kind === 'week') { return [WEEK_FROM, WEEK_TO]; }
        // THE MONTH THE ANCHOR IS IN, not the grid around it - the
        // same decision SL-7 took for the shopping list, so a month
        // means one thing on this screen.
        var p = ANCHOR.split('-');
        var y = Number(p[0]), m = Number(p[1]) - 1;
        return [iso(new Date(y, m, 1)), iso(new Date(y, m + 1, 0))];
    }

    document.addEventListener('click', function (ev) {
        var b = ev.target && ev.target.closest
            && ev.target.closest('.cp-preset');
        if (!b) { return; }
        var two = span(b.getAttribute('data-cp-span'));
        if (el('cpFrom')) { el('cpFrom').value = two[0]; }
        if (el('cpTo')) { el('cpTo').value = two[1]; }
        [].forEach.call(document.querySelectorAll('.cp-preset'),
            function (x) { x.setAttribute('aria-pressed',
                x === b ? 'true' : 'false'); });
    });

    // OPENS ON THIS WEEK, because that is what the old dialog copied
    // and the commonest thing to want. Nothing is landed until a
    // landing date is typed, which has no sensible default.
    //
    // NO jQUERY HERE - CP-2, 21 Oct 2026. The first draft bound this
    // with $('#copyRangeModal').on('show.bs.modal', ...) and the
    // browser said `$ is not defined`: base loads jQuery near the END
    // of the document, so a parse-time $ binds nothing. That is
    // RL-1's finding from 20 October, in a new costume - a guard
    // answers "is it here?", not "will it be?" - and it was found the
    // same way, by driving the dialog rather than reading it.
    //
    // Set now, because the inputs are parsed by the time this runs,
    // and re-set on every open, because a cancelled dialog leaves
    // whatever was last typed in it.
    function seed() {
        if (el('cpFrom') && !el('cpFrom').value) {
            el('cpFrom').value = WEEK_FROM;
            el('cpTo').value = WEEK_TO;
        }
    }
    seed();
    document.addEventListener('click', function (ev) {
        var o = ev.target && ev.target.closest
            && ev.target.closest('[data-target="#copyRangeModal"]');
        if (o) { seed(); copyPreview(); }
    });

    // SAY SO FIRST - MW-1's decision, 19 Oct 2026, kept.
    //
    // "Add alongside, AND SAY SO FIRST" is not the same decision as
    // "add alongside": a dialog that cannot count what is already
    // there is the same copy with a quieter conscience. MW-1's week
    // dialog asked, and the first draft of this round dropped the
    // question along with the dialog. test_meal_week said so.
    //
    // The button is enabled by the ANSWER. Nothing a user typed
    // enables it, so a copy cannot go ahead while the count is still
    // in flight.
    function days(a, b) {
        return Math.round((Date.parse(b) - Date.parse(a)) / 86400000);
    }

    function copyPreview() {
        var note = el('cpNote'), go = el('cpGo');
        if (!note || !go) { return; }
        go.disabled = true;
        var f = el('cpFrom').value, t = el('cpTo').value,
            o = el('cpOnto').value;
        if (!f || !t || !o) { note.innerHTML = ''; return; }
        var span = days(f, t);
        if (span < 0) { span = -span; }
        var end = new Date(Date.parse(o) + span * 86400000);
        var onto_to = iso(end);
        if (!(Date.parse(o) > Date.parse(t)
              || Date.parse(onto_to) < Date.parse(f))) {
            note.innerHTML = '<div class="alert alert-warning">'
                + 'Those days overlap the ones being copied. Pick a '
                + 'landing date outside them.</div>';
            return;
        }
        note.innerHTML = '<p class="text-muted">'
            + '<i class="fas fa-spinner fa-spin"></i> '
            + 'Checking those days...</p>';
        // THE HEADER OBJECT ON ITS OWN LINE, so the literal does
        // not end on two closing braces with nothing between them.
        // test_meal_week balances Django's variable delimiters
        // across the whole page to catch an unclosed tag, and a
        // JavaScript object that happens to end that way is counted
        // as one - a false close that the page pays for.
        //
        // AND THIS NOTE DOES NOT SPELL IT EITHER. The first version
        // explained the problem by quoting it, and the detector read
        // the explanation: 169 opens against 171 closes, both of the
        // extras in these six lines. Tenth instance of the house's
        // oldest trap - a thing and something that merely names the
        // thing are not two things.
        fetch(PREVIEW + '?from=' + encodeURIComponent(o)
              + '&to=' + encodeURIComponent(onto_to), {
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (!d.success) {
                // NOT alert() - SL-4. A browser dialog blocks every
                // event after it, and this dialog has a place to say
                // things.
                note.innerHTML = '<div class="alert alert-warning">'
                    + d.error + '</div>';
                return;
            }
            if (d.meals === 0) {
                note.innerHTML = '<div class="alert alert-info">'
                    + '<strong>' + d.label + '</strong> is empty. '
                    + 'The copy lands on clear days.</div>';
            } else {
                // THE COUNT, IN WORDS, BEFORE THE BUTTON. Nothing is
                // replaced and nothing is skipped: a day that had a
                // dinner and gains another has two, visibly, which is
                // a thing you can fix. A silent repair is not.
                note.innerHTML = '<div class="alert alert-warning">'
                    + '<strong>' + d.label + '</strong> already has '
                    + d.meals + ' meal' + (d.meals === 1 ? '' : 's')
                    + ' on ' + d.days_with_meals + ' day'
                    + (d.days_with_meals === 1 ? '' : 's') + '. '
                    + 'The copy is <strong>added alongside</strong> '
                    + 'them - nothing is removed or replaced.</div>';
            }
            go.disabled = false;
        })
        .catch(function () {
            note.innerHTML = '<div class="alert alert-warning">Those '
                + 'days could not be checked. Check your connection '
                + 'and try again.</div>';
        });
    }

    ['cpFrom', 'cpTo', 'cpOnto'].forEach(function (id) {
        if (el(id)) { el(id).addEventListener('change', copyPreview); }
    });
    [].forEach.call(document.querySelectorAll('.cp-preset'),
        function (b) { b.addEventListener('click', copyPreview); });
    copyPreview();
}());
</script>
'''

COPY_CSS = '''
/* THE COPY DIALOG - CP-2, 21 Oct 2026. */
.cp-presets { display: flex; flex-wrap: wrap; gap: 8px; }
.cp-presets .btn { height: 44px; }
.cp-preset[aria-pressed="true"] {
    background: var(--alv-accent-soft);
    border-color: var(--alv-accent-line);
    color: var(--alv-accent-ink);
}
.cp-dates { display: flex; gap: 12px; }
.cp-dates .form-group { flex: 1 1 0; min-width: 0; }
@media screen and (max-width: 767px) {
    .cp-dates { flex-direction: column; gap: 0; }
}

/* THE MENUS DIALOG - two sections, two forms, one dialog. */
.mn-section + .mn-section {
    margin-top: 18px;
    padding-top: 18px;
    border-top: 1px solid var(--alv-line);
}
.mn-head {
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--alv-ink-soft);
    margin-bottom: 10px;
}
'''


# =====================================================================
# THE MENUS DIALOG - save, apply and delete in one place
# =====================================================================
# TWO SIBLING FORMS, NOT ONE. They post to different endpoints and a
# form cannot nest, so the dialog holds two - which is also why
# Delete finally has a home instead of being a trashcan inside Apply.
MENUS_MODAL = '''{# ============================================== saved menus #}
{# ONE DIALOG FOR THE WHOLE IDEA - CP-2, 21 Oct 2026.               #}
{#                                                                  #}
{# Save-as-a-Menu and Apply-a-Menu are two halves of one thing: a   #}
{# named set of meals kept by weekday. They were two dialogs behind #}
{# two items in a menu no desktop could open. Delete was a trashcan #}
{# buried inside Apply, which is why it had nowhere to be described. #}
{#                                                                  #}
{# TWO SIBLING FORMS, because they post to different endpoints and  #}
{# a form cannot nest. Both endpoints are untouched by this round.  #}
<div class="modal fade" id="menusModal" tabindex="-1" role="dialog"
     aria-labelledby="menusLabel" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="menusLabel">
                    <i class="fas fa-bookmark"></i> Saved Menus
                </h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">

                <div class="mn-section">
                    <div class="mn-head">Save this week as a menu</div>
                    <form method="POST" action="{% url 'save_menu' %}">
                        {% csrf_token %}
                        <input type="hidden" name="view" value="{{ view_mode }}">
                        <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">
                        <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
                        <p class="text-muted" style="font-size:13px;">
                            The meals on <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>
                            are kept under a name, by weekday, so the same
                            week can be stamped onto any week later.
                        </p>
                        <div class="form-group">
                            <label for="saveMenuName"><strong>Name</strong></label>
                            <input type="text" class="form-control" id="saveMenuName"
                                   name="name" maxlength="100" autocomplete="off"
                                   placeholder="e.g. Easy Winter Week" required>
                        </div>
                        <button type="submit" class="btn action-secondary">
                            <i class="fas fa-bookmark"></i> Save this week
                        </button>
                    </form>
                </div>

                <div class="mn-section">
                    <div class="mn-head">Your menus</div>
                    <form method="POST" action="{% url 'apply_menu' %}">
                        {% csrf_token %}
                        <input type="hidden" name="view" value="{{ view_mode }}">
                        <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">
                        <input type="hidden" name="week" value="{{ week_start|date:'Y-m-d' }}">
                        <input type="hidden" name="menu_id" id="applyMenuId">
                        {% if menus %}
                        <p class="text-muted" style="font-size:13px;">
                            The menu you pick is added to
                            <strong>{{ week_start|date:"j M" }} &ndash; {{ week_end|date:"j M" }}</strong>,
                            alongside whatever is already there.
                        </p>
                        <div class="menu-list">
                            {% for menu in menus %}
                            <div class="menu-option" data-menu-id="{{ menu.menu_id }}"
                                 onclick="pickMenu(this)">
                                <div class="menu-option-name">
                                    <strong>{{ menu.name }}</strong><br>
                                    <small class="text-muted">
                                        {{ menu.item_count }} meal{{ menu.item_count|pluralize }}
                                    </small>
                                </div>
                                <div class="row-actions">
                                    <button type="button" class="icon-action-btn icon-delete"
                                            title="Delete this menu"
                                            aria-label="Delete the menu {{ menu.name }}"
                                            onclick="deleteMenu(event, {{ menu.menu_id }}, '{{ menu.name|escapejs }}')"><i class="fas fa-trash"></i></button>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        <button type="submit" class="btn action-primary" id="applyMenuGo" disabled>
                            <i class="fas fa-check"></i> Add to This Week
                        </button>
                        {% else %}
                        {# THE EMPTY STATE SAYS WHERE MENUS COME FROM, and  #}
                        {# now it can point UP rather than at a dialog the  #}
                        {# reader cannot see from here.                     #}
                        <div class="empty-day">
                            <i class="fas fa-list-ul"></i>
                            <p>No menus yet.</p>
                            <p class="text-muted">
                                Put some meals on a week, then use
                                <strong>Save this week</strong> above.
                            </p>
                        </div>
                        {% endif %}
                    </form>
                </div>

            </div>
            <div class="modal-footer">
                <button type="button" class="btn action-secondary" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

'''


def menu_twins(code):
    """Menu items whose target exists nowhere outside the menu.

    THE REVERSE OF HP-1's QUESTION. That round asked whether every bar
    secondary has a twin IN the menu, because base hides secondaries
    on a phone. This asks whether every menu item has a twin OUTSIDE
    it, because base hides the MENU on a desktop. Both directions had
    to be asked; only one of them was.
    """
    cut = code.find('action-more-menu')
    if cut < 0:
        return []
    outside, menu = code[:cut], code[cut:]
    end = menu.find('</div>', menu.rfind('action-more-item')) \
        if 'action-more-item' in menu else 0
    menu, after = menu[:end], menu[end:]
    outside = outside + after
    lost = []
    for b in re.finditer(r'<(?:button|a)\b[^>]*class="[^"]*'
                         r'\baction-more-item\b[^"]*"[^>]*>', menu):
        tag = b.group(0)
        m = re.search(r'data-target="#([\w-]+)"', tag)
        key = ('#' + m.group(1)) if m else ''
        if not key:
            m = re.search(r"url '([\w_]+)'", tag)
            key = m.group(1) if m else ''
        if key and key not in outside:
            lost.append(key)
    return lost


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'BACK ON THE BAR - CP-2' in t:
        print('CP-2  already applied - Copy and Saved Menus are on the bar.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)

    # ---- THE FINDING, MEASURED. The three features must really be
    # menu-only right now, or this round is aimed at a tree that has
    # already moved.
    lost = menu_twins(code)
    want = {'#copyWeekModal', '#saveMenuModal', '#applyMenuModal'}
    if set(lost) != want:
        refuse('%s: the menu-only items are %r, and this round is about '
               '%r' % (TPL, sorted(lost), sorted(want)))

    # ---- THE ENGINE IT LEANS ON, asked by name.
    pv = os.path.join(root, VIEW)
    v = read(pv)
    vcode = T.python_code_only(v, payloads=True)
    for probe, why in (('def copy_week_rows', 'the copy engine'),
                       ('def planner_back', 'where a write returns to'),
                       ('def day_label', 'how a date is spoken'),
                       ('def week_of', 'reading a date from a post')):
        if probe not in vcode:
            refuse('%s: %s is missing (%s)' % (VIEW, probe, why))
    if 'def copy_meal_range' in vcode:
        refuse('%s: copy_meal_range already exists' % VIEW)

    # ---- THE VIEW AND THE ROUTE
    v = swap(v, VIEW_WAS, VIEW_NOW, '%s (the range copy)' % VIEW)
    v = swap(v, PREVIEW_WAS, PREVIEW_NOW, '%s (the range preview)' % VIEW)
    out[pv] = v
    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), URL_WAS, URL_NOW, '%s (the route)' % URLS)

    # ---- THE BAR AND THE MENU
    t = swap(t, BAR_WAS, BAR_NOW, '%s (the two secondaries)' % TPL)
    t = swap(t, MENU_WAS, MENU_NOW, '%s (the menu twins)' % TPL)

    # ---- THE DIALOGS. The two old menu dialogs become one, and the
    # week-shaped copy becomes a range-shaped one. Cut newest-first so
    # the offsets of the earlier ones are still good.
    spans = sorted((modal(t, 'copyWeekModal'),
                    modal(t, 'saveMenuModal'),
                    modal(t, 'applyMenuModal')), reverse=True)
    for i, j in spans:
        t = t[:i] + t[j:]
    # and the two new ones go where the first of them was
    at = min(s[0] for s in spans)
    t = t[:at] + COPY_MODAL + MENUS_MODAL + t[at:]

    # ---- ITS CSS AND ITS SCRIPT
    t = swap(t, '\n.month-grid {\n    display: grid;',
             COPY_CSS + '\n.month-grid {\n    display: grid;',
             '%s (the dialog CSS)' % TPL)
    # ANCHORED, NOT APPENDED. The first draft read
    #     t = t.rstrip() + COPY_JS + '{% endblock %}' if ... else t
    # which added a SECOND {% endblock %} after the one already there,
    # and Django refused the template at line 4102. A swap on the one
    # anchor cannot do that: `once()` would have refused if the anchor
    # were ambiguous, and the text is replaced rather than extended.
    t = swap(t, '\n{% render_help_modal "meal_plans" %}\n{% endblock %}',
             COPY_JS + '\n{% render_help_modal "meal_plans" %}\n'
             '{% endblock %}', '%s (the preset script)' % TPL)

    # ---- AND THE HANDLERS THAT ADDRESSED THE DIALOGS THAT WENT
    t = cut(t, DEAD_JS_AT, DEAD_JS_END, DEAD_JS_NOW,
            '%s (the dead handlers)' % TPL)
    out[pt] = t

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_bar_audit.py'
)""", """    'test_bar_audit.py',
    # CP-2, 21 Oct 2026 - three features that could only be reached
    # on a phone are on the bar, and Copy takes any span of days.
    'test_copy_menus.py'
)""", '%s (the suites)' % PS1)
    # MW-1's THREE SENTINELS NAME THREE DIALOGS THIS ROUND DELETES.
    # A sentinel pointed at a string a round renamed stops the push
    # BEFORE any suite runs - and twenty-two suites in the tree check
    # that every sentinel still resolves, so leaving them would turn
    # one change into twenty-two red suites. It did, in the 21 Oct
    # sweep, which is how this was found.
    s = swap(s, """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="copyWeekModal"'; What = 'MW-1: a week can be copied onto a week you pick' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="saveMenuModal"'; What = 'MW-1: and saved under a name, by weekday' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="applyMenuModal"'; What = 'MW-1: and a saved Menu stamped onto any week' },""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="copyRangeModal"'; What = 'MW-1, as CP-2 left it: any span of days can be copied onto a landing date - a day, a week, a month or a range you type' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="menusModal"'; What = 'MW-1, as CP-2 left it: a week saved under a name by weekday, applied to any week, and deleted - all three in one dialog' },""",
             '%s (MW-1 sentinels)' % PS1)
    s = swap(s,
             """    @{ File = 'test_bar_order.py'; Text = 'A BAR IS NOT ALWAYS A <div>';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'BACK ON THE BAR - CP-2'; What = 'CP-2: Copy... and Saved Menus... are bar buttons, so they can be reached on a desktop - MW-1 put all three week controls inside the More menu, which base hides above 768px, and for two days they existed only on a phone' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def copy_meal_range('; What = 'CP-2: a copy takes any span of days onto a landing date - day, week and month are presets that fill in two dates, because copy_week_rows has always worked by date offset' },
    @{ File = 'test_bar_order.py'; Text = 'A BAR IS NOT ALWAYS A <div>';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    # ---- THE GUIDE. A help tab that describes three controls nobody
    # can find is worse than one that says nothing: MH-3's whole point
    # is that the guide and the screen are checked against each other,
    # and test_meal_guide3 asks both sides of every sentence.
    ph = os.path.join(root, HELP)
    h = read(ph)
    h = swap(h, HELP_INTRO_WAS, HELP_INTRO_NOW, '%s (the intro)' % HELP)
    h = swap(h, HELP_CARDS_WAS, HELP_CARDS_NOW, '%s (the controls)' % HELP)
    h = swap(h, HELP_COUNT_WAS, HELP_COUNT_NOW, '%s (the count)' % HELP)
    h = swap(h, HELP_PERMS_WAS, HELP_PERMS_NOW, '%s (the permission)' % HELP)
    h = swap(h, HELP_TIP_WAS, HELP_TIP_NOW, '%s (the tip)' % HELP)
    out[ph] = h

    # ---- THE PINS OTHER ROUNDS LEFT, MOVED IN THIS PATCHER
    for name, old, new, why in PINS:
        pp2 = os.path.join(root, name)
        out[pp2] = swap(out.get(pp2, read(pp2)), old, new,
                        '%s (%s)' % (name, why))

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # BA-1, 21 Oct 2026 - the instrument that could not see the bar.
    'test_bar_audit.py',
]""", """    # BA-1, 21 Oct 2026 - the instrument that could not see the bar.
    'test_bar_audit.py',
    # CP-2, 21 Oct 2026 - Copy and Saved Menus, reachable at last.
    'test_copy_menus.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # BA-1, 21 Oct 2026 - three holes in the bar instrument.
    '.bak_baraudit',
]""", """    # BA-1, 21 Oct 2026 - three holes in the bar instrument.
    '.bak_baraudit',
    # CP-2, 21 Oct 2026 - a copy of any span, and menus with a door.
    '.bak_copymenus',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # CP-2, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    left = menu_twins(nc)
    if left:
        refuse('%s: still reachable only on a phone: %r' % (TPL, left))
    for mid in ('copyWeekModal', 'saveMenuModal', 'applyMenuModal'):
        if mid in nc:
            refuse('%s: %s survived - the old dialogs are replaced, not '
                   'left beside the new ones' % (TPL, mid))
    for mid in ('copyRangeModal', 'menusModal'):
        if nc.count('id="%s"' % mid) != 1:
            refuse('%s: %s appears %d time(s), expected 1'
                   % (TPL, mid, nc.count('id="%s"' % mid)))
    # BOTH ENDPOINTS SURVIVE INSIDE THE NEW DIALOG. A merge that lost
    # one would pass every count above.
    mm = nc[nc.index('id="menusModal"'):]
    mm = mm[:mm.index('id="copyRangeModal"')] if 'id="copyRangeModal"' \
        in mm else mm
    for u in ("url 'save_menu'", "url 'apply_menu'"):
        if u not in mm:
            refuse('%s: the menus dialog lost %s' % (TPL, u))
    if 'deleteMenu(' not in mm:
        refuse('%s: the menus dialog lost the delete control' % TPL)
    # THE BAR GAINED EXACTLY TWO SECONDARIES, and is still in house
    # order - BO-1 put the primary first this morning.
    bar = nc[nc.index('page-action-buttons'):nc.index('action-more-menu')]
    roles = [k for m in re.finditer(r'class="btn (action-[a-z]+)"', bar)
             for k in [m.group(1)]]
    seq = ''.join({'action-primary': 'P', 'action-secondary': 'S',
                   'action-filter': 'F', 'action-back': 'B'}.get(r, '')
                  for r in roles)
    if not re.match(r'^P*S*F*B*$', seq):
        refuse('%s: the bar reads %r, which is not house order'
               % (TPL, seq))
    if seq.count('S') != 4:
        refuse('%s: %d secondaries in the bar, expected 4 - Copy, '
               'Saved Menus, Print and Help' % (TPL, seq.count('S')))
    # AND THE VIEW REUSES THE ENGINE RATHER THAN COPYING IT.
    nv = T.python_code_only(out[pv], payloads=True)
    seg = nv[nv.index('def copy_meal_range'):]
    seg = seg[:seg.index('\ndef ', 1)] if '\ndef ' in seg[1:] else seg
    if 'copy_week_rows(' not in seg:
        refuse('%s: copy_meal_range does not use the existing engine, '
               'so leftovers will not follow their parents' % VIEW)
    if 'MealEntry.objects' not in seg:
        refuse('%s: copy_meal_range fetches nothing' % VIEW)
    if '(end - start).days > 92' not in seg:
        refuse('%s: copy_meal_range has no ceiling, and three other '
               'pages that take a span have the same one' % VIEW)

    if CHECK:
        print('CP-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        menu-only features: %d -> %d' % (len(lost),
                                                        len(left)))
        print('        the bar: %s' % seq)
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CP-2  applied - Copy and Saved Menus are on the bar.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
