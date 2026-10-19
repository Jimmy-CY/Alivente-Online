# -*- coding: utf-8 -*-
"""apply_meal_guide3.py - round MH-3, 19 Oct 2026.

RELEASE 3, PUSH 2. THE GUIDE CATCHES UP WITH THE WEEK.

Demetri's standing instruction on release 3: "You will also need to
fully update the help sections of the whole meal plan module !!"

MH-2 DID THAT YESTERDAY, FOR THE PLANNER. It rewrote three tabs,
dropped the one that described a screen MN-1 retired, and reworded two
more. It also wrote a promise, at the foot of the Adding a Meal tab:

    "Not yet, and coming: repeating a whole week onto another, saved
    menus, a free-text note on a day, and marking a meal as leftovers.
    Moving a meal from one day to another comes with them."

MW-1 AND MO-1 BUILT FOUR OF THOSE FIVE THINGS THIS MORNING. A guide
that promises what the application already does is worse than one that
says nothing: a reader who believes it will not go looking for the
control, and the controls are the whole point of the push.

WHAT THIS ROUND DOES

    A NEW TAB - Moving a Week. Copy this week to..., Save this week as
    a Menu, Apply a Menu, and where the three live (behind the More
    menu on the bar) and what collisions do. Seven tabs where MH-2
    left six, and the two suite pins that count them move with it.

    ADDING A MEAL grows the note row and leftovers, which belong there
    - they are things you add to a DAY - and its promise box is
    rewritten to promise only the one thing still outstanding.

    TWO TIPS, on the two features most likely to go unused because
    nobody knew they were free: a Menu applied in December was saved
    in October, and three nights of one pot is bought once.

    AND A GATE WITH NO EXCEPTION IN IT. PROMISED_WORDS is the mirror
    of MH-2's RETIRED_WORDS: that register holds the words of screens
    the planner no longer has, and this one holds the words of
    features it now DOES have, asserted absent from any sentence that
    calls something "coming". MH-2's own absence gate caught its
    author naming Duplicate in the Overview prose - "a gate with an
    exception in it is a gate somebody will widen" - and this one is
    built the same way.

WHAT IS STILL OUTSTANDING, AND SAID SO HONESTLY: moving a meal from
one day to another, and reordering a day. Those are push 3.

Idempotent. Every file backed up to .bak_mealguide3.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_mealguide3'
HELP = os.path.join('pages', 'help_content', 'administration.html')
MH = 'test_meal_help.py'
ME = 'test_meal_guide3.py'
PATCHER = 'apply_meal_guide3.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
SLUG = 'meal_plans'
MARK = 'MH-3, 19 Oct 2026'
TABS_WAS_N = 6
TABS_NOW_N = 7
CHECK = False

# THE WORDS OF FEATURES THAT NOW EXIST. Asserted absent from any
# sentence that calls something coming - see the gate in main() and the
# register this round adds to test_meal_help.
BUILT = ('repeating a whole week', 'saved menus',
         'a free-text note on a day', 'marking a meal as leftovers')


# ============================================================ THE NEW TAB
WEEK_TAB = """<article data-tab-slug="mp-week"
           data-tab-name="Moving a Week"
           data-tab-icon="fa-copy">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-copy" style="color:#28a745;"></i> Copying a week, and saving one</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;">Three controls, and all three sit behind the <strong><i class="fas fa-ellipsis-v"></i></strong> button on the planner's own bar &mdash; beside Shopping List and Help. They act on <strong>the week on screen</strong>, so pick the week first.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-copy" style="color:#28a745;"></i> Copy this week to&hellip;</strong> Pick any day in the week you want and every meal on screen lands on the matching weekday of that week, with the servings it was cooked for. Nothing stays linked afterwards &mdash; change the new week and the old one does not move.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-bookmark" style="color:#0e7c8b;"></i> Save this week as a Menu.</strong> Give the week a name and it is kept <strong>by weekday</strong> rather than by date. That is the difference between a Menu and a copy: a week you save in October can be applied to a week in December, because what is stored is &ldquo;Monday, Thursday, Sunday&rdquo; and not three dates in October.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list-ul" style="color:#0e7c8b;"></i> Apply a Menu&hellip;</strong> Choose one from the list and its meals are added to the week on screen. The menu itself is unchanged &mdash; applying it is a stamp, not a move, so the same menu can be used every month. Each row says how many meals it holds, and carries a <strong>trashcan</strong> to forget it.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-layer-group" style="color:#e6a817;"></i> Two meals landing on one day gives you two meals.</strong> Nothing is replaced and nothing is skipped. Before <strong>Copy the Week</strong> can be pressed, the dialog counts what the target week already holds and tells you &mdash; so a day that ends up with two dinners is something you chose and can see, rather than something that happened quietly.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-redo" style="color:#0e7c8b;"></i> Leftovers travel with their meal.</strong> Copy a week that has leftovers on it and they point at the copy of the meal they came from, not back at the old week &mdash; so the new week is still bought exactly once. A Menu does not keep leftovers at all: a leftover is a consequence of a particular week, not something you plan in advance.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #dc3545; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-ban" style="color:#dc3545;"></i> Deleting a Menu does not delete any meals.</strong> The meals an Apply put on your weeks are real meals on real dates, with no link back. Forgetting the menu leaves every week you used it on exactly as it was.
      </div>

    </div>

    <div style="background:#fff3cd; border:1px solid #ffeeba; border-radius:8px; padding:12px; font-size:13px; color:#856404;">
      <i class="fas fa-user-lock"></i> <strong>You need editing rights.</strong> A reader can see the week and shop from it, but the <strong><i class="fas fa-ellipsis-v"></i></strong> button is not there without permission to edit recipes.
    </div>
  </article>

  """


# ======================================== ADDING A MEAL - TWO MORE BLOCKS
BUILD_WAS = """      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper and the day cards are all built for a narrow screen, which is where a week usually gets planned.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Not yet, and coming:</strong> repeating a whole week onto another, saved menus, a free-text note on a day, and marking a meal as leftovers. Moving a meal from one day to another comes with them.
    </div>"""

BUILD_NOW = """      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-store" style="color:#28a745;"></i> Add Note, for a night you are not cooking.</strong> Eat out, takeaway, at a friend's. It sits on the day like a meal does, so the week reads as a plan rather than as a plan with holes in it &mdash; and it buys nothing: a note never reaches the shopping list. Three suggestions are offered so a planned night is one tap.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-redo" style="color:#0e7c8b;"></i> Leftovers, and they are free.</strong> The <strong><i class="fas fa-redo"></i></strong> button beside a meal puts it on another day as leftovers. <strong>It costs nothing on the shopping list</strong> &mdash; you bought the ingredients on the night you cooked &mdash; so a pot of soup that feeds you three times is bought once. The leftover row names the day it was cooked on and has no servings stepper, because changing that number would buy nothing.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper, the two Add buttons and the day cards are all built for a narrow screen, which is where a week usually gets planned.
      </div>

    </div>

    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Not yet, and coming:</strong> moving a meal from one day to another, and reordering the meals on a day. Everything else this tab used to list as coming is now on the <strong>Moving a Week</strong> tab or above.
    </div>"""


# ============================================================== TWO TIPS
TIPS_WAS = """      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-mobile-alt"></i> It works on a phone.</strong> Every screen here does, including the picker and the dialogs. The shopping list in particular is meant to be read in the shop.
      </div>"""

TIPS_NOW = """      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-bookmark"></i> Save the weeks you come back to.</strong> A Menu is kept by weekday, so the Christmas week, the week the family visits and the ordinary rotation can each be saved once and applied whenever they come round. That is what a Menu is for; <strong>Copy this week to&hellip;</strong> is for last week.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-redo"></i> Use leftovers &mdash; they are free.</strong> Marking the second and third night as leftovers of the first means the shopping list buys that pot once instead of three times. It is the single biggest difference you can make to what a week costs, and it takes two taps.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-mobile-alt"></i> It works on a phone.</strong> Every screen here does, including the picker and the dialogs. The shopping list in particular is meant to be read in the shop.
      </div>"""


# ========================================================== THE OVERVIEW
# MH-2's Overview enumerates what the planner does. Four new controls
# is not a detail it can leave out.
OVER_WAS = """Past dates are allowed"""


# ===================================================== THE SUITE, RE-PINNED
MH_TABS_WAS = """# MH-2, 18 Oct 2026 - SEVEN BECAME SIX. 'The Plan Page' went with the
# plan page, and 'Building a Plan' is 'Adding a Meal', because you add a
# meal to a day now rather than building a container first.
TABS = ('Overview', 'The Calendar', 'Adding a Meal',
        'Shopping List', 'Who Can Do What', 'Tips')"""

MH_TABS_NOW = """# MH-2, 18 Oct 2026 - SEVEN BECAME SIX. 'The Plan Page' went with the
# plan page, and 'Building a Plan' is 'Adding a Meal', because you add a
# meal to a day now rather than building a container first.
#
# MH-3, 19 Oct 2026 - AND SIX BECAME SEVEN AGAIN, which is a different
# seven: 'Moving a Week' is the three controls MW-1 shipped - copy a
# week, save one as a Menu, apply a Menu - and they are not 'Adding a
# Meal', because they act on a WEEK. The six above are MH-2's own and
# none of them left.
TABS = ('Overview', 'The Calendar', 'Adding a Meal', 'Moving a Week',
        'Shopping List', 'Who Can Do What', 'Tips')"""

# AND THE MESSAGE THAT SAID SEVEN WHILE COUNTING SIX. MH-1 wrote
# 'seven tabs, in order' and MH-2 took the number to six without
# touching the sentence, so for a day the guide's own suite printed a
# number that was not the one it was asserting. It is read off TABS
# now, which cannot drift.
MH_SEVEN_WAS = """    ok(got == list(TABS), 'seven tabs, in order', got)"""
MH_SEVEN_NOW = """    ok(got == list(TABS), '%d tabs, in order' % len(TABS), got)"""

# THE MIRROR OF RETIRED_WORDS. That register holds the words of screens
# the planner no longer has; this one holds the words of features it
# now DOES have, and the claim is that no sentence in the guide calls
# any of them coming. MH-2's absence gate caught its own author naming
# Duplicate in the Overview, so this one is built the same way - no
# exception in it, because a gate with an exception is a gate somebody
# will widen.
MH_PROMISE_WAS = """    ok(len(mod['tabs']) == len(TABS),
       '  across all %d tab(s)' % len(TABS), len(mod['tabs']))"""

MH_PROMISE_NOW = """    ok(len(mod['tabs']) == len(TABS),
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
                      'marking a meal as leftovers')
    coming = [s for s in re.split(r'(?<=[.!])\\s+', whole)
              if 'coming' in s.lower() or 'not yet' in s.lower()]
    stale = sorted(w for w in PROMISED_WORDS
                   for s in coming if w in s)
    ok(not stale,
       'the guide promises nothing it already does - none of the %d '
       'features MW-1 and MO-1 shipped' % len(PROMISED_WORDS), stale)
    # AND THE CONTROLS REALLY ARE THERE, asked of the planner. An
    # absence claim on its own would pass on a guide that simply never
    # mentions them.
    for text, what in (("id=\\"copyWeekModal\\"", 'Copy this week to'),
                       ("id=\\"saveMenuModal\\"", 'Save this week as a Menu'),
                       ("id=\\"applyMenuModal\\"", 'Apply a Menu'),
                       ("id=\\"noteModal\\"", 'Add Note'),
                       ("id=\\"leftoverModal\\"", 'Leftovers')):
        ok(text in T.code_only(plan_src),
           '  CONTROL: the planner really has %s' % what)
    # AND THE GUIDE DESCRIBES EVERY ONE OF THEM. A tab that exists is
    # not the same as a tab that says the thing.
    for phrase in ('Copy this week to', 'Save this week as a Menu',
                   'Apply a Menu', 'Add Note', 'Leftovers'):
        ok(phrase in whole, '  and the guide describes %r' % phrase)
    # THE ONE THING STILL OUTSTANDING IS STILL PROMISED, honestly. A
    # round that cleared the promise box by emptying it would pass
    # every check above and tell the reader less.
    ok(any('moving a meal from one day to another' in s.lower()
           for s in coming),
       '  while what is NOT built is still named as coming', coming[:2])"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'check_gates.py'; Text = 'name, taken, declared, referenced = nm'; What = 'NF-1: and the caller reads all four answers' },"""
SENT_NOW = """    @{ File = 'check_gates.py'; Text = 'name, taken, declared, referenced = nm'; What = 'NF-1: and the caller reads all four answers' },
    # ------------------------------------------------- MH-3, 19 Oct 2026
    @{ File = 'pages/help_content/administration.html'; Text = 'data-tab-name="Moving a Week"'; What = 'MH-3: the guide has a tab for copying a week and saving a Menu' },
    @{ File = 'pages/help_content/administration.html'; Text = 'Leftovers, and they are free'; What = 'MH-3: and tells the reader the second night costs nothing' },
    @{ File = 'pages/help_content/administration.html'; Text = 'coming:</strong> repeating a whole week'; Absent = $true; Code = $true; What = 'MH-3: and no longer promises four things MW-1 and MO-1 have built' },"""

SUITE_WAS = """    'test_name_free.py'
)"""
SUITE_NOW = """    'test_name_free.py',
    # MH-3, 19 Oct 2026 - release 3, push 2. The guide catches up
    # with the week. MH-2 promised four features at the foot of a
    # tab and MW-1 and MO-1 built all four the next morning.
    'test_meal_guide3.py'
)"""

TREE_WAS = """    'test_name_free.py',
]"""
TREE_NOW = """    'test_name_free.py',
    # MH-3, 19 Oct 2026 - the guide catches up with the week. Wide
    # from birth: the promise gate reads every tab of the module.
    'test_meal_guide3.py',
]"""

RD_WAS = """    '.bak_namefree',
]"""
RD_NOW = """    '.bak_namefree',
    # MH-3, 19 Oct 2026 - the guide catches up with the week. Demetri's
    # standing instruction on release 3: the help sections of the whole
    # meal plan module are part of the release, not a follow-up to it.
    '.bak_mealguide3',
]"""

WD_WAS = """CONVERTED_N = 109   # NF-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 110   # MH-3, 19 Oct 2026 - this round own suite   # (was 109)   # NF-1, 19 Oct 2026 - this round own suite"""


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
    raise SystemExit('MH-3 REFUSED: %s' % msg)


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

    BY THE SLUG, as MH-2 did. administration.html carries sixteen
    modules and two of them have the word Recipe in a comment banner;
    the slug is what the renderer keys on and the only thing in the
    file unique by construction.
    """
    i = text.find('<section data-module-slug="%s"' % SLUG)
    if i < 0:
        refuse('%s: no module with slug %r' % (HELP, SLUG))
    j = text.find('</section>', i)
    if j < 0:
        refuse('%s: the %r module never closes' % (HELP, SLUG))
    return i, j


def articles(block):
    out = []
    for m in re.finditer(r'<article data-tab-slug="([^"]+)"', block):
        start = m.start()
        end = block.find('</article>', start)
        if end < 0:
            refuse('%s: tab %r never closes' % (HELP, m.group(1)))
        out.append((m.group(1), start, end + len('</article>')))
    return out


def after_article(text, slug, new):
    """Put a whole <article> immediately after the one named by slug."""
    i, j = module_of(text)
    block = text[i:j]
    hits = [a for a in articles(block) if a[0] == slug]
    if len(hits) != 1:
        refuse('%s: tab %r appears %d time(s), expected exactly 1'
               % (HELP, slug, len(hits)))
    _s, _a, b = hits[0]
    # The gap after an </article> is '\n\n  ' in this file; keep it, so
    # the inserted tab sits the same way its siblings do.
    tail = block[b:]
    gap = len(tail) - len(tail.lstrip('\r\n '))
    return (text[:i] + block[:b] + tail[:gap] + fit(text, new)
            + tail[gap:] + text[j:])


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    ph = os.path.join(root, HELP)
    h = read(ph)
    h_before = h

    # ---------------------------------------------------------------- 0
    if 'data-tab-name="Moving a Week"' in h:
        print('MH-3  already applied - the guide describes the week.')
        return 0

    # ---------------------------------------------------------------- 1
    # MW-1 AND MO-1 MUST BOTH BE APPLIED. This round describes what
    # they built; run against a tree without them it would write a
    # guide to controls nobody can press, which is the exact fault it
    # exists to remove, pointing the other way.
    tpl = os.path.join(root, 'pages', 'templates', 'meal_planner.html')
    if not os.path.isfile(tpl):
        refuse('meal_planner.html is not in the tree. Apply MN-1 first.')
    planner = read(tpl)
    for text, who in (('id="copyWeekModal"', 'MW-1'),
                      ('id="saveMenuModal"', 'MW-1'),
                      ('id="applyMenuModal"', 'MW-1'),
                      ('id="noteModal"', 'MO-1'),
                      ('id="leftoverModal"', 'MO-1')):
        if text not in planner:
            refuse('the planner has no %s. MH-3 describes %s\'s controls; '
                   'apply %s first.' % (text, who, who))

    i, j = module_of(h)
    names = [a[0] for a in articles(h[i:j])]
    if len(names) != TABS_WAS_N:
        refuse('%s: the %s module has %d tab(s), expected %d - the guide '
               'has moved since this round was written'
               % (HELP, SLUG, len(names), TABS_WAS_N))
    if 'mp-week' in names:
        refuse('%s: a mp-week tab already exists' % HELP)

    # ---------------------------------------------------------------- 2
    h = after_article(h, 'mp-build', WEEK_TAB.rstrip() + '\n\n  ')
    h = swap(h, BUILD_WAS, BUILD_NOW, '%s (Adding a Meal)' % HELP)
    h = swap(h, TIPS_WAS, TIPS_NOW, '%s (Tips)' % HELP)

    # ---------------------------------------------------------------- 3
    # SEVEN TABS, AND THE ORDER IS THE READING ORDER.
    i, j = module_of(h)
    block = h[i:j]
    names = [a[0] for a in articles(block)]
    if len(names) != TABS_NOW_N:
        refuse('%s: the rewrite leaves %d tab(s), expected %d'
               % (HELP, len(names), TABS_NOW_N))
    want = ['mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
            'mp-shopping', 'mp-permissions', 'mp-tips']
    if names != want:
        refuse('%s: the tabs read %s, expected %s' % (HELP, names, want))

    # NOTHING THE APPLICATION DOES IS DESCRIBED AS COMING. The gate
    # with no exception in it, run on the module's own prose - and
    # scoped to the sentences that call something coming, because the
    # new tab says "repeating a whole week" is exactly what Copy does.
    coming = [s for s in re.split(r'(?<=[.!])\s+', block)
              if 'coming' in s.lower() or 'not yet' in s.lower()]
    stale = sorted(w for w in BUILT for s in coming if w in s)
    if stale:
        refuse('%s: the guide still promises %s - MW-1 and MO-1 built '
               'every one of those this morning'
               % (HELP, ', '.join(repr(w) for w in stale)))
    # AND WHAT IS NOT BUILT IS STILL PROMISED. A round that cleared the
    # box by emptying it would pass the gate above and tell the reader
    # less than MH-2 did.
    if not any('moving a meal from one day to another' in s.lower()
               for s in coming):
        refuse('%s: nothing is named as coming any more. Moving a meal '
               'between days is push 3 and the reader should be told so.'
               % HELP)
    out[ph] = h

    # ---------------------------------------------------------------- 4
    pm = os.path.join(root, MH)
    m = read(pm)
    m = swap(m, MH_TABS_WAS, MH_TABS_NOW, '%s (the tab names)' % MH)
    m = swap(m, MH_SEVEN_WAS, MH_SEVEN_NOW, '%s (the tab count)' % MH)
    m = swap(m, MH_PROMISE_WAS, MH_PROMISE_NOW, '%s (the promise gate)' % MH)
    out[pm] = m

    # ---------------------------------------------------------------- 5
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pr = os.path.join(root, TREE)
    out[pr] = swap(read(pr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 6
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    # THE DELTA, NOT THE BALANCE - MH-2's lesson. administration.html
    # has never balanced <article> by raw count, because three of its
    # opens are inside prose that shows markup. What must hold is that
    # this round adds exactly ONE tab: one open and one close.
    d_open = out[ph].count('<article') - h_before.count('<article')
    d_close = out[ph].count('</article>') - h_before.count('</article>')
    if (d_open, d_close) != (1, 1):
        refuse('%s: the rewrite changed the tab count by %d open and %d '
               'close, expected 1 and 1' % (HELP, d_open, d_close))
    d_div = out[ph].count('<div') - h_before.count('<div')
    d_dive = out[ph].count('</div>') - h_before.count('</div>')
    if d_div != d_dive:
        refuse('%s: this round opens %d <div> and closes %d - an unclosed '
               'div in a help tab eats the tabs after it'
               % (HELP, d_div, d_dive))

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('MH-3 --check')
        print('  tabs       : %d -> %d' % (TABS_WAS_N, TABS_NOW_N))
        print('  order      : %s' % ', '.join(want))
        print('  files      : %d' % len(out))
        for k in sorted(out):
            print('    %s' % os.path.relpath(k, root))
        print('--check: nothing written.')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
        print('  wrote %s' % os.path.relpath(k, root))
    print('MH-3  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_meal_help.py && python test_meal_guide3.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
