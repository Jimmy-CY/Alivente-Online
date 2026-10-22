# -*- coding: utf-8 -*-
"""apply_help_agrees.py - round HG-1, 22 Oct 2026.

THE GUIDE DESCRIBED A FEATURE THAT NO LONGER EXISTS, AND A SUITE WAS
HOLDING IT THERE.

Demetri, 22 October, with push 5 on GitHub and not yet deployed:

    "Have you updated the Recipes / Meal Plans Help ?? with the latest
     changes??"

NO. RO-1 updated the one sentence three suites pin. MN-2 rebuilt the
whole Saved Menus feature and changed none of the prose, so the
Moving a Week tab still says:

    "Save this week keeps the week on screen under a name - BY WEEKDAY
     rather than by date ... what is stored is Monday, Thursday, Sunday"

Every clause of that is now false. Save takes a From and a To, any span
to 92 days; what is stored is a DAY OFFSET from the first day of the
range - a Christmas menu starting Wednesday 23 December stores 0, 2 and
9, which are not weekdays; and Apply lands on a date you choose rather
than on the week on screen.

AND test_meal_guide3 REQUIRED THE STALE SENTENCE:

    c['  that a Menu is kept BY WEEKDAY, which is the whole point'] = (
        'by weekday' in w.lower())

That is worse than a gap. The suite was not merely failing to notice
the drift; it was enforcing it. MN-2 could not have corrected the guide
without that claim going red, and the claim was written when it was
true.

WHY NOTHING CAUGHT IT. test_meal_help, test_meal_guide3 and
test_meal_guide5 ask both sides of the sentences they NAME. Prose they
do not name can say anything at all. A round that changes a feature is
never asked whether the guide still describes it.

SO THIS ROUND ADDS THE QUESTION, IN BOTH DIRECTIONS - and the shape of
it was measured rather than guessed, because the first two shapes were
useless:

  1 EVERY BOLD STRING MUST BE A CONTROL. Measured across all 39 help
    modules: 1,706 failures, almost all of them prose emphasis - "1st
    of the current month", "Always have a backup", "Column 1:". A gate
    that cries 1,706 times is a gate nobody reads.

  2 A NEAR MISS IS A RENAME. Measured: 68 pairs, almost all accidental
    - "Green" against "Agreement", "Sent" against "Set". And the one
    real defect, "Save this week" against "Save these days", scored
    just UNDER the cutoff. A gate tuned so the true case is borderline
    is not a gate.

  3 WHAT IS HERE. Two questions, each exact:

      GUIDE -> PAGE   a label the guide marks as a CONTROL - <strong
                      class="ui"> - must be the text of a real control
                      on a page that renders this module. Exact match,
                      no guessing. Marking is opt-in and grows as tabs
                      are touched, so it starts honest and small.

      PAGE -> GUIDE   every control on the page's own ACTION BAR must
                      be named somewhere in the module. No marking
                      needed. This is the direction that catches a
                      feature arriving and never being written up, and
                      it found two today.

THE SECOND DIRECTION FOUND TWO MORE. The shopping list's bar carries
Generate List and Save Conversions & Generate List, and the guide names
neither. Both are in this round.

HELP IS EXEMPT, and the reason is written into the register rather than
left as a silent special case: the guide is what the Help button opens,
so a guide describing its own button is a mirror.

THE TAB KEEPS ITS NAME. "Moving a Week" is loose now that a menu is a
span, but it is pinned in four places across two suites and renaming it
buys nothing this round is for. Recorded rather than done.

Idempotent. Every file backed up to .bak_helpagrees.
"""
import os
import re
import sys

SUFFIX = '.bak_helpagrees'
GUIDE = os.path.join('pages', 'help_content', 'administration.html')
G3 = 'test_meal_guide3.py'
ME = 'test_help_agrees.py'
PATCHER = 'apply_help_agrees.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'HG-1, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE SAVED MENUS BLOCK - every clause of it was false
# ==========================================================================
MENUS_WAS = """        <strong style="color:#2c3e50;"><i class="fas fa-bookmark" style="color:#0e7c8b;"></i> Saved Menus.</strong> One dialog, three things. <strong>Save this week</strong> keeps the week on screen under a name &mdash; <strong>by weekday</strong> rather than by date, which is the difference between a Menu and a copy: a week saved in October can be applied to a week in December, because what is stored is &ldquo;Monday, Thursday, Sunday&rdquo; and not three dates in October. <strong>Your menus</strong> lists what you have saved and adds the one you pick to the week on screen &mdash; a stamp, not a move, so the same menu can be used every month. Each row says how many meals it holds and carries a <strong>trashcan</strong> to forget it."""

MENUS_NOW = """        <strong style="color:#2c3e50;"><i class="fas fa-bookmark" style="color:#0e7c8b;"></i> Saved Menus.</strong> One dialog, three things. <strong class="ui">Save these days</strong> keeps a stretch of days under a name &mdash; <strong class="ui">From</strong> and <strong class="ui">To</strong>, with the same <strong class="ui">This day</strong>, <strong class="ui">This week</strong> and <strong class="ui">This month</strong> presets Copy has, up to 92 days. What is stored is <strong>how far into the menu each day falls</strong> and not a date, which is the difference between a Menu and a copy: a Christmas menu built on 23 December is kept as &ldquo;day 1, day 3, day 10&rdquo; and can be stamped onto any dates at all. <strong>Your menus</strong> lists what you have saved, each row saying how many meals it holds and over how many days, and carries a <strong>trashcan</strong> to forget it. Pick one, set <strong class="ui">Landing on</strong> to the day it should start, and the line underneath tells you which days it will cover before you press <strong class="ui">Add to These Days</strong> &mdash; a stamp, not a move, so the same menu can be used every month."""

# ---- and the tab's opening line, which still called it a week
INTRO_WAS = """    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-copy" style="color:#28a745;"></i> Copying a week, and saving one</h6>"""

INTRO_NOW = """    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-copy" style="color:#28a745;"></i> Copying days, and saving them</h6>"""

# ---- the two bar controls the second direction found
SHOP_WAS = """      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-balance-scale"></i> Fix the base units once.</strong>"""

SHOP_NOW = """      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-list-check"></i> Generate List builds it.</strong> Pick the days and press <strong class="ui">Generate List</strong>: the list is the meals on those days with their ingredients added up. If anything needs a unit the system does not know yet, <strong class="ui">Set base units</strong> opens the conversions and <strong class="ui">Save Conversions &amp; Generate List</strong> saves what you type and builds the list in one press, so there is nothing to come back and start again.
      </div>

      <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
        <strong><i class="fas fa-balance-scale"></i> Fix the base units once.</strong>"""


# ---- AND THE TIPS TAB SAID IT TOO. Two tabs carried the same stale
# clause; correcting one and leaving the other is how a guide ends up
# disagreeing with itself.
TIPS_WAS = """        <strong><i class="fas fa-bookmark"></i> Save the weeks you come back to.</strong> A Menu is kept by weekday, so the Christmas week, the week the family visits and the ordinary rotation can each be saved once and applied whenever they come round. That is what a Menu is for; <strong>Copy&hellip;</strong> is for last week - or any stretch of days, onto any date."""

TIPS_NOW = """        <strong><i class="fas fa-bookmark"></i> Save the days you come back to.</strong> A Menu is kept by how far into it each day falls, so Christmas and New Year, the week the family visits and the ordinary rotation can each be saved once &mdash; over as many days as they really take &mdash; and stamped onto whatever dates they fall on this year. That is what a Menu is for; <strong class="ui">Copy&hellip;</strong> is for last week, or any stretch of days, onto any date."""

# ==========================================================================
# test_meal_guide3 - the claim that REQUIRED the stale sentence
# ==========================================================================
G3_WAS = """    c['  that a Menu is kept BY WEEKDAY, which is the whole point'] = (
        'by weekday' in w.lower())"""

G3_NOW = """    # HG-1, 22 Oct 2026 - THIS CLAIM WAS HOLDING THE GUIDE WRONG.
    # MW-1 wrote it when it was true: a Menu really was kept by
    # weekday. MN-2 made a Menu a span of days kept by OFFSET on 21
    # October and could not have corrected the guide without this
    # going red - so the guide was not corrected. A suite that pins
    # the wording of a feature outlives the feature unless the round
    # that changes the feature is the round that moves the pin.
    c['  that a Menu is kept by HOW FAR INTO IT each day falls'] = (
        'how far into the menu' in w.lower()
        and 'by weekday' not in w.lower())"""

# ---- AND THE PIN ON THAT TIP. Same shape as the weekday one: a suite
# naming the exact wording of a tip about a feature, written when the
# feature was a week. It is the third pin in this round that would
# have had to move for the guide to tell the truth, and the reason the
# gate this round adds asks about CONTROLS rather than prose: a control
# label is a fact, and a sentence is a sentence.
G3_TIP_WAS = """    c['the tips tell you to save the weeks you come back to'] = (
        'Save the weeks you come back to' in t)"""

G3_TIP_NOW = """    # HG-1, 22 Oct 2026 - days, not weeks. MN-2 made a Menu a span.
    c['the tips tell you to save the days you come back to'] = (
        'Save the days you come back to' in t)"""



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
    raise SystemExit('HG-1 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pg = os.path.join(root, GUIDE)
    g = read(pg)

    if MARK in g:
        print('HG-1  already applied - the guide and the page agree.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, ASKED OF THE GUIDE. If the stale clause is not
    # there this round is being applied to a tree that already moved.
    if 'by weekday' not in g:
        refuse('%s: the stale clause this round corrects is not there'
               % GUIDE)
    if 'Save this week' not in g:
        refuse('%s: the stale control label is not there' % GUIDE)

    g = swap(g, INTRO_WAS, INTRO_NOW, '%s (the heading)' % GUIDE)
    g = swap(g, MENUS_WAS, MENUS_NOW, '%s (Saved Menus)' % GUIDE)
    g = swap(g, SHOP_WAS, SHOP_NOW, '%s (the shopping bar)' % GUIDE)
    g = swap(g, TIPS_WAS, TIPS_NOW, '%s (the tips tab)' % GUIDE)
    out[pg] = g

    p3 = os.path.join(root, G3)
    g3 = read(p3)
    g3 = swap(g3, G3_WAS, G3_NOW, '%s (the weekday pin)' % G3)
    g3 = swap(g3, G3_TIP_WAS, G3_TIP_NOW, '%s (the tip pin)' % G3)
    out[p3] = g3

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_recipe_tidy.py'
)""", """    'test_recipe_tidy.py',
    # HG-1, 22 Oct 2026 - the guide names what the page shows, and the
    # page's bar is named in the guide. Both directions.
    'test_help_agrees.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/view_recipe.html'; Text = 'NOT A DATA TABLE';""",
             """    @{ File = 'pages/help_content/administration.html'; Text = 'how far into the menu'; What = 'HG-1: the Moving a Week tab describes the feature MN-2 actually shipped - a menu is a span of days kept by offset, saved with a From and a To and landed on a date you choose. It said by weekday, and test_meal_guide3 was requiring it to' },
    @{ File = 'pages/templates/view_recipe.html'; Text = 'NOT A DATA TABLE';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # VR-1, 21 Oct 2026 - the schedule readout, measured onto tokens.
    'test_recipe_tidy.py',
]""", """    # VR-1, 21 Oct 2026 - the schedule readout, measured onto tokens.
    'test_recipe_tidy.py',
    # HG-1, 22 Oct 2026 - the guide and the page agree, both ways.
    'test_help_agrees.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # VR-1, 21 Oct 2026 - the recipe schedule readout onto tokens.
    '.bak_recipetidy',
]""", """    # VR-1, 21 Oct 2026 - the recipe schedule readout onto tokens.
    '.bak_recipetidy',
    # HG-1, 22 Oct 2026 - the guide describes what shipped.
    '.bak_helpagrees',
]""", '%s (ROUNDS)' % ROUNDS)

    pwd = os.path.join(root, WD)
    wd = read(pwd)
    n = re.search(r'CONVERTED_N = (\d+)', wd)
    out[pwd] = swap(wd, 'CONVERTED_N = %s' % n.group(1),
                    'CONVERTED_N = %d   # HG-1, 22 Oct 2026 - this round '
                    'own suite   # (was %s)'
                    % (int(n.group(1)) + 1, n.group(1)),
                    '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    ng = out[pg]
    # THE STALE CLAUSES ARE GONE, ALL OF THEM.
    for dead in ('by weekday', 'Save this week',
                 'Monday, Thursday, Sunday'):
        if dead in ng:
            refuse('%s: %r survived' % (GUIDE, dead))
    # AND THE TRUE ONES ARE THERE.
    for live in ('how far into the menu', 'Save these days',
                 'Landing on', 'Add to These Days', 'Generate List',
                 'Save Conversions'):
        if live not in ng:
            refuse('%s: the guide does not say %r' % (GUIDE, live))
    # EVERY MARKED LABEL IS A REAL CONTROL. The gate this round adds,
    # run here as well so a half-written block cannot be applied.
    labels = set(re.findall(r'<strong class="ui">(.*?)</strong>', ng, re.S))
    if len(labels) < 8:
        refuse('%s: only %d marked label(s) - the round marks the ones '
               'it writes' % (GUIDE, len(labels)))
    import html as _h
    pages = [p for p in T.templates()
             if re.search(r'\{%\s*render_help_modal\s+"meal_plans"\s*%\}',
                          read(p))]
    if len(pages) != 2:
        refuse('%d page(s) render the meal_plans module, expected 2'
               % len(pages))
    have = set()
    for p in pages:
        code = T.code_only(read(p))
        # A CONTROL IS NOT ONLY A BUTTON. The first draft of this
        # gate read <button> and <a> and refused From, To and Landing
        # on - which are <label> elements on real fields the guide is
        # right to name. A gate that calls a correct sentence wrong is
        # the same fault as one that misses a wrong one.
        for m in re.finditer(
                r'<(?:button|a|label|option)\b[^>]*>(.*?)'
                r'</(?:button|a|label|option)>', code, re.S):
            lbl = _h.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))
            lbl = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', '', lbl)
            lbl = re.sub(r'\s+', ' ', lbl).strip()
            if lbl:
                have.add(lbl.lower())
    ghost = sorted(x for x in labels
                   if _h.unescape(x).strip().lower() not in have)
    if ghost:
        refuse('%s: the guide marks %r as a control and no page that '
               'renders this module has it' % (GUIDE, ghost))

    if CHECK:
        print('HG-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        %d marked label(s), all of them real controls'
              % len(labels))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('HG-1  applied - the guide describes the feature that shipped.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
