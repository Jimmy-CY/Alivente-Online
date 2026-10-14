# -*- coding: utf-8 -*-
"""apply_panel_heads.py - round PH-2, 14 Oct 2026.

A STATUS COLOUR USED AS DECORATION IS A STATUS COLOUR THAT HAS STOPPED
MEANING ANYTHING.

Demetri, looking at the live site: "why do we have Green in the WCIM? And
green in the Pantry Staples? And green in the ingredient families? Are we
happy that the colours in the Results are correct?"

Three questions and one answer. Those headers are
`class="card-header bg-success text-white"`, and base.html ALREADY pulls
every one of them onto a house token:

    bg-success  ->  --alv-good     #1e7d4f   a POSITIVE STATUS
    bg-warning  ->  --alv-warn     #8e6207   needs attention
    bg-info     ->  --alv-accent   #0e7c8b   the BRAND / ACTION colour
    bg-light    ->  (not overridden)  #f8f9fa - and --alv-surface is #f8f9fa

So the green is not a stray Bootstrap green. It is house-coloured and
semantically WRONG: the success colour, as decoration, on panels that
report no success.

NAMED PH-2. PH-1 is the passport-holder round and PH-1c is cited inside
backfill_passport_holder.py, so this takes the next free number in that
family rather than reusing one. Checked: PH-2 appears in no file.

THE INVENTORY IS 21 ON 12 PAGES, AND MY FIRST TWO ANSWERS WERE LOW
-------------------------------------------------------------------
I told Demetri "14 on 10 pages", then "20 occurrences of five names".
Both were mine and both were wrong. Asked of every element carrying a
bg-* utility rather than of the names I had guessed at: 21 on 12. Sorted
by what each one is FOR, which is the only sort that decides anything:

    5   card header as CHROME                       -> house card head
    2   card header as STATUS, correct              -> keep
    1   card header as status, WRONG TIER           -> quiet
    1   card header, danger, doing its job          -> keep, named
    3   progress-bar bg-info                        -> record
    7   bg-light panels and rows                    -> one line in base
    2   bg-info panel fills, property side          -> record

WHY .alv-card AND NOT .form-card, WHICH IS COMMONER
----------------------------------------------------
.form-card is 119 cards on 53 pages against .alv-card's 64 on 9, so
frequency says the wrong thing. Measured: .form-card is FORM FURNITURE -
50 of its 53 pages carry a <form>, and the three that do not are
access_denied, password_set_done and password_set_invalid, which are
confirmation screens. .alv-card is the house panel for a screen that is
not a form: asset_detail, property_assets, the dashboard, petty_cash,
lease_renewal_report, tenant_report, vacancy_management.

These five recipe screens are a chooser, two lists of chips and a list of
families. None is a form.

AND NOT .alv-card-lead EITHER. That class is for "the FIRST card on a
detail screen [that] names the thing the page is about" - base's own
words, three uses on three detail screens. The WCIM landing is a chooser
whose <h1> already says WHAT CAN I MAKE?; a lead card would say it twice.

THE RESULTS PAGE IS HALF RIGHT, AND THE WRONG HALF IS THE INTERESTING ONE
--------------------------------------------------------------------------
Make Now green and Almost There amber are doing real status work and are
LEFT ALONE. Worth Shopping For is wrong on three counts, in order of
weight:

  1. bg-info is --alv-accent, the colour every primary button in this
     application wears. A section header in the action colour tells the
     eye to press it.
  2. The tier FURTHEST from cookable is the loudest thing on a list that
     is sorted best-first.
  3. A three-step scale should go somewhere. Green, amber, teal is not a
     progression - it ends by jumping hue. Green, amber, quiet is one.

TWO THINGS MEASUREMENT TURNED UP THAT THE SURVEY DID NOT START WITH
--------------------------------------------------------------------
pantry_staples is green at TWO levels. Each of the 92 staple chips
carries style="background: #f0fff4;" - the page's only hex literal, not a
house token, and invisible to every colour census in this project because
it is an inline style. Base already defines --alv-good-soft: #e6f4ec.

    THOSE TWO GREENS ARE NOT THE SAME COLOUR. #f0fff4 is brighter and
    bluer. This is a REAL VISIBLE CHANGE and not a rename, which is why
    it was rendered at 1180 and 390 before it was proposed, and why
    Demetri decided it rather than me.

bg-light is the opposite: Bootstrap's value is #f8f9fa and --alv-surface
is #f8f9fa, IDENTICAL. One declaration in base makes the utility
house-owned at zero visual cost, and it is exactly the move base already
made for its three siblings. Rewriting seven markup sites for the same
pixels would be worse - two of them are <tr> inside a table and one is a
card bg-light.

    THIS CONTRADICTS WHAT I TOLD DEMETRI, which was "no base.html
    change". It is one declaration, it moves no pixel, and it closes the
    last bg-* hole rather than leaving it to reopen - the same argument
    that put btn-outline-dark on VC-1's list while nothing used it. He
    decided it.

WHAT IS NOT TOUCHED, AND IS NAMED RATHER THAN LEFT INVISIBLE
--------------------------------------------------------------
  projects/projects_delete  bg-danger on Confirm Project Deletion. The
                            one of the nine where the colour is doing its
                            job.
  wcim_results              Make Now green, Almost There amber.
  3 progress bars           project_gantt, projects, projects_detail. A
                            meter filled with the brand colour is not
                            chrome and not a status; deciding it is a
                            different round.
  2 property-side fills     total_expense_details' Grand Total and
                            projects_detail's Greek translations panel
                            are the same mistake one module over.
                            Demetri: name them, leave them.

See test_panel_heads.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_panelheads'
SUITE = 'test_panel_heads.py'
BASE = 'base.html'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

N_HEADS, N_PAGES = 6, 5
N_CHIP_LITERAL = 1
N_BG_TOTAL, N_BG_PAGES = 21, 12
N_KEPT = 3          # projects_delete danger, Make Now, Almost There

CONVERTED_WAS, CONVERTED_NOW = 76, 77
ALIAS_WAS, ALIAS_NOW = 63, 65
ALIAS_P_WAS, ALIAS_P_NOW = 31, 32
ALIAS_S_WAS, ALIAS_S_NOW = 32, 33

EDITS = [
    ('wcim_landing.html',
     '<div class="card mb-3">\r\n      <div class="card-header bg-success text-white">\r\n        <h5 class="mb-0"><i class="fas fa-bullseye"></i> Pick your anchor(s)</h5>\r\n      </div>\r\n      <div class="card-body">',
     '<div class="alv-card mb-3">\r\n      <div class="alv-card-head">\r\n        <i class="fas fa-bullseye"></i>\r\n        <span class="alv-card-title">Pick your anchor(s)</span>\r\n      </div>\r\n      <div class="alv-card-body">',
     'Pick your anchor(s) - a chooser, not a success'),
    ('wcim_extras.html',
     '<div class="card mb-3">\r\n      <div class="card-header bg-info text-white">\r\n        <h5 class="mb-0"><i class="fas fa-list-ul"></i> Optional extras</h5>\r\n      </div>\r\n      <div class="card-body">',
     '<div class="alv-card mb-3">\r\n      <div class="alv-card-head">\r\n        <i class="fas fa-list-ul"></i>\r\n        <span class="alv-card-title">Optional extras</span>\r\n      </div>\r\n      <div class="alv-card-body">',
     'Optional extras - the accent used as chrome'),
    ('wcim_results.html',
     '<div class="card mb-4">\r\n      <div class="card-header bg-info text-white">\r\n        <h5 class="mb-0">\r\n          <i class="fas fa-shopping-cart"></i> Worth Shopping For\r\n          <span class="badge badge-light ml-2">{{ tier_groups.worth_shopping|length }}</span>\r\n        </h5>\r\n      </div>\r\n      <div class="card-body">',
     '<div class="alv-card mb-4">\r\n      <div class="alv-card-head">\r\n        <i class="fas fa-shopping-cart"></i>\r\n        <span class="alv-card-title">Worth Shopping For</span>\r\n        <span class="alv-card-aside alv-tag">{{ tier_groups.worth_shopping|length }}</span>\r\n      </div>\r\n      <div class="alv-card-body">',
     'the THIRD tier - the least ready, and the loudest'),
    ('pantry_staples.html',
     '<div class="card mb-4">\r\n    <div class="card-header bg-success text-white">\r\n      <h5 class="mb-0"><i class="fas fa-check-circle"></i> Your Staples</h5>\r\n    </div>\r\n    <div class="card-body">',
     '<div class="alv-card mb-4">\r\n    <div class="alv-card-head">\r\n      <i class="fas fa-check-circle"></i>\r\n      <span class="alv-card-title">Your Staples</span>\r\n    </div>\r\n    <div class="alv-card-body">',
     'Your Staples'),
    ('pantry_staples.html',
     '<div class="card mb-4">\r\n    <div class="card-header bg-info text-white">\r\n      <h5 class="mb-0"><i class="fas fa-plus-circle"></i> Add an Ingredient</h5>\r\n    </div>\r\n    <div class="card-body">',
     '<div class="alv-card mb-4">\r\n    <div class="alv-card-head">\r\n      <i class="fas fa-plus-circle"></i>\r\n      <span class="alv-card-title">Add an Ingredient</span>\r\n    </div>\r\n    <div class="alv-card-body">',
     'Add an Ingredient'),
    ('ingredient_families.html',
     '<div class="card mb-3">\r\n      <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">\r\n        <h6 class="mb-0">\r\n          <i class="fas fa-layer-group"></i> {{ family.name }}\r\n          <span class="badge badge-light ml-2">{{ family.members.all|length }}</span>\r\n        </h6>\r\n        <div class="row-actions">',
     '<div class="alv-card mb-3">\r\n      <div class="alv-card-head">\r\n        <i class="fas fa-layer-group"></i>\r\n        <span class="alv-card-title">{{ family.name }}</span>\r\n        <span class="alv-tag">{{ family.members.all|length }}</span>\r\n        <div class="alv-card-aside row-actions">',
     'a family card - this one renders 28 times'),
    ('ingredient_families.html',
     '          </form>\r\n        </div>\r\n      </div>\r\n      <div class="card-body">',
     '          </form>\r\n        </div>\r\n      </div>\r\n      <div class="alv-card-body">',
     'and that card body'),
    ('pantry_staples.html',
     'style="background: #f0fff4;"',
     'style="background: var(--alv-good-soft);"',
     'the 92 staple chips - the page only hex literal'),
]

# ---------------------------------------------------------------------------
# base.html - ONE declaration, and it moves no pixel
# ---------------------------------------------------------------------------
# Bootstrap's .bg-light is #f8f9fa. --alv-surface is #f8f9fa. Identical. So
# this changes nothing on screen and everything about ownership: the utility
# stops being Bootstrap's and starts being the token's, which is exactly what
# base already did for bg-info, bg-success and bg-warning three rounds ago.
#
# SEVEN SITES USE IT - act_expense, projects_delete, projects_detail x2,
# property_detail, total_expense_details x2 - and two of those seven are <tr>
# elements inside a table while one is a `card bg-light`. Rewriting them to
# reach the same pixels is seven edits across five pages against one line.
BASE_WAS = """      .bg-warning { background-color: var(--alv-warn) !important; }"""

BASE_NOW = """      .bg-warning { background-color: var(--alv-warn) !important; }
      /* AND .bg-light, PH-2, 14 Oct 2026 - A RENAME, NOT A RECOLOUR.
         Bootstrap's value is #f8f9fa and --alv-surface is #f8f9fa, so this
         declaration moves no pixel anywhere. What it moves is OWNERSHIP:
         seven sites across five pages were using a Bootstrap utility whose
         value happened to match the house token, and a value that matches
         by coincidence stops matching the day the token is tuned.
         The same move this file already made for its three siblings above. */
      .bg-light { background-color: var(--alv-surface) !important; }"""

# ---------------------------------------------------------------------------
# test_cssrules_outside.py / test_neutrals.py - one more hex literal leaves
# ---------------------------------------------------------------------------
# The 92 pantry chips were the LAST colour literal on that page, so CR-1's
# census of inline style= colours comes down by one and pantry_staples drops
# out of its page list entirely. B-5b asserts the same two numbers from
# inside test_neutrals, for the reason written beside it: "This is the gate
# B-4's push failed on: it moved four of CR-1's census numbers and left
# them."
#
# BOTH NUMBERS GO DOWN, WHICH IS WHY THEY ARE REWRITTEN AND NOT RELAXED. A
# pin that only ever loosens asserts nothing.
CSS = 'test_cssrules_outside.py'
NEU = 'test_neutrals.py'

CSS_MARKUP_WAS = """MARKUP_STYLE = 88      # colour literals in inline style= attributes"""
CSS_MARKUP_NOW = """MARKUP_STYLE = 87      # colour literals in inline style= attributes   # PH-2, 14 Oct 2026 - pantry_staples' 92 staple chips carried #f0fff4 inline; they carry var(--alv-good-soft) now, and that page has no hex literal left at all.   # (was 88)"""

CSS_PAGES_WAS = """PAGES = 36              # real pages carrying any of them"""
CSS_PAGES_NOW = """PAGES = 35              # real pages carrying any of them   # PH-2 - and it was pantry_staples' ONLY one, so the page leaves this census   # (was 36)"""

NEU_WAS = """for want in ('MARKUP_STYLE = 88', 'SCRIPT = 148', 'PAGES = 36',"""
NEU_NOW = """# PH-2, 14 Oct 2026 - two more of the six move, and down. The pantry
# chips were the last inline colour literal on their page.
for want in ('MARKUP_STYLE = 87', 'SCRIPT = 148', 'PAGES = 35',"""

# ---------------------------------------------------------------------------
# test_important_base.py - ONE more !important, and it is the right kind
# ---------------------------------------------------------------------------
# The .bg-light declaration carries !important because the Bootstrap rule it
# beats carries one. DW-1's suite counts them and its own closing check says
# what makes one acceptable: "every one of them is beating Bootstrap or a
# sibling rule, not base - which is what !important is for in a Bootstrap
# application". This one beats `.bg-light{background-color:#f8f9fa!important}`
# in the vendor stylesheet and nothing else, so it passes that check and only
# the counts move.
IMP = 'test_important_base.py'

IMP_BASE_WAS = """IMP_BASE = 73"""
IMP_BASE_NOW = """IMP_BASE = 74   # PH-2, 14 Oct 2026 - .bg-light onto var(--alv-surface). It carries !important because the Bootstrap rule it beats carries one, which is the only reason this file accepts any of them.   # (was 73)"""

IMP_TREE_WAS = """IMP_TREE = 857   # MH-2, 13 Oct 2026 - suppliers' one"""
IMP_TREE_NOW = """IMP_TREE = 858   # PH-2, 14 Oct 2026 - the .bg-light line in base   # (was 857)   # MH-2, 13 Oct 2026 - suppliers' one"""

# ---------------------------------------------------------------------------
# test_vocabulary.py - VC-1's suite, three repairs, and I wrote two of them
# wrong ONE DAY after repairing the identical checks in somebody else's
# ---------------------------------------------------------------------------
# VC-1 asserts the row-action pair is in .row-actions by matching the EXACT
# attribute `class="row-actions"`. PH-2 made it `class="alv-card-aside
# row-actions"` - the pair is still in .row-actions and the inline style is
# still gone, so VC-1's claim is still true and only its string match broke.
# Repaired to test the class TOKEN, which is both correct and stricter: a
# page that renamed the wrapper would still fail.
#
# AND THE OTHER TWO ARE MINE, TWICE OVER. `CONVERTED == N` and
# `ROUNDS[-1] == SUFFIX` are true for exactly one day each. RS-1a repaired
# both of those checks inside E11's suite on 13 Oct; RS-1b repaired them
# again inside its own on 14 Oct - and I wrote them into VC-1 the same
# afternoon. A floor and an ORDER, for the third time.
VOC = 'test_vocabulary.py'

VOC_RA_WAS = """ok('class="row-actions"' in _if and 'display: flex; gap: 6px;' not in _if,
   'ingredient_families wraps its pair in .row-actions, and the inline '
   'style is gone')"""
VOC_RA_NOW = """# THE TOKEN, NOT THE ATTRIBUTE - repaired by PH-2, 14 Oct 2026. This read
# `class="row-actions"` exactly, and PH-2 made the wrapper
# `class="alv-card-aside row-actions"`: the pair is still in .row-actions
# and the inline style is still gone, so the claim held and only the match
# broke. Splitting the class list is also stricter than either - a page
# that renamed the wrapper to `row-actions-wide` still fails here, which a
# substring match would not notice.
#
# AND NO BACKSLASH IN THE NEEDLE, WHICH IS NOT STYLE. The first repair
# wrote a word-boundary regex, and this text is a PAYLOAD inside a
# non-raw triple-quoted string in apply_panel_heads.py: the two
# characters backslash-b became a literal BACKSPACE in the file it wrote,
# and the check failed against a page it was sitting in. Same family as
# the docstring escaping that broke test_surface_border.py on 13 Oct.
ok([c for _cl in re.findall('class="([^"]*)"', _if)
    for c in _cl.split() if c == 'row-actions']
   and 'display: flex; gap: 6px;' not in _if,
   'ingredient_families wraps its pair in .row-actions, and the inline '
   'style is gone')"""

VOC_CONV_WAS = """ok(len(alv_tree.CONVERTED) == CONVERTED_NOW,
   '  CONVERTED holds %d' % CONVERTED_NOW, len(alv_tree.CONVERTED))"""
VOC_CONV_NOW = """# A FLOOR, NOT AN EQUALITY - PH-2, 14 Oct 2026, and this is the third
# round to make this repair in six days.
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))"""

VOC_ROUNDS_WAS = """ok(SUFFIX in ROUNDS and ROUNDS[-1] == SUFFIX,
   '%s is the newest entry in alv_rounds.ROUNDS' % SUFFIX, ROUNDS[-3:])"""
VOC_ROUNDS_NOW = """# AN ORDER, NOT "NEWEST" - PH-2, 14 Oct 2026. "Newest" is true for one
# day. RS-1a repaired this exact check inside E11's suite, RS-1b inside
# its own, and VC-1 was written with it the same afternoon.
ok(SUFFIX in ROUNDS and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_rsb'),
   '%s is in alv_rounds.ROUNDS, after RS-1b' % SUFFIX, ROUNDS[-3:])"""

# ---------------------------------------------------------------------------
# the registers
# ---------------------------------------------------------------------------
TREE_WAS = """    # VC-1, 14 Oct 2026 - the gate's VOCABULARY, after RS-1b widened
    # its page scope. Wide from birth, same shape as RS-1b's.
    'test_vocabulary.py',
]"""
TREE_NOW = """    # VC-1, 14 Oct 2026 - the gate's VOCABULARY, after RS-1b widened
    # its page scope. Wide from birth, same shape as RS-1b's.
    'test_vocabulary.py',
    # PH-2, 14 Oct 2026 - the panel heads. Demetri asked why three
    # recipe screens were green; the answer was a status token used
    # as decoration. Wide from birth.
    'test_panel_heads.py',
]"""

ROUNDS_WAS = """    # VC-1, 14 Oct 2026 - BTN gains a tag, BOOTSTRAP two colours,
    # POSITION one house name, and _scan asks the register before
    # it gives up on a button.
    '.bak_vocab',
]"""
ROUNDS_NOW = """    # VC-1, 14 Oct 2026 - BTN gains a tag, BOOTSTRAP two colours,
    # POSITION one house name, and _scan asks the register before
    # it gives up on a button.
    '.bak_vocab',
    # PH-2, 14 Oct 2026 - six panel heads off the status palette
    # and onto the house card, and .bg-light onto --alv-surface.
    '.bak_panelheads',
]"""

SUITE_WAS = """    'test_vocabulary.py'
)"""
SUITE_NOW = """    'test_vocabulary.py',
    'test_panel_heads.py'
)"""

CLAIMS_ANCHOR = """    @{ File = 'pages\\templates\\create_meal_plan.html'; Text = 'btn.style.background'; What = 'and no JavaScript paints it any more'; Absent = $true; Code = $true },"""

CLAIMS = """    @{ File = 'pages\\templates\\create_meal_plan.html'; Text = 'btn.style.background'; What = 'and no JavaScript paints it any more'; Absent = $true; Code = $true },
    # ------------------------------------------------- PH-2, 14 Oct 2026
    # Demetri asked why three recipe screens were green. Because a STATUS
    # token was being used as decoration - base already mapped bg-success
    # onto --alv-good, so they were house-coloured and semantically wrong.
    @{ File = 'pages\\templates\\base.html'; Text = '.bg-light { background-color: var(--alv-surface)'; What = 'the last Bootstrap background utility is house-owned - a rename, not a recolour' },
    @{ File = 'pages\\templates\\ingredient_families.html'; Text = 'alv-card-head'; What = 'and 28 family cards stop wearing the success colour as chrome' },
    @{ File = 'pages\\templates\\wcim_results.html'; Text = 'bg-info'; What = 'the least-ready tier stops being the loudest thing on the page'; Absent = $true; Code = $true },
    # AND NOT A SENTINEL FOR "Almost There KEEPS the amber". It was
    # written as one and test_sentinels refused it, correctly: bg-warning
    # is in all eight backed-up versions of that file, so the row could
    # never fail and therefore asserted nothing. A sentinel catches a
    # REGRESSION in something this round changed. "I deliberately did not
    # touch this" belongs in the round's own suite, and section 2 of
    # test_panel_heads.py says it there, with the reason attached.
    @{ File = 'pages\\templates\\pantry_staples.html'; Text = 'var(--alv-good-soft)'; What = 'and 92 pantry chips leave a hex literal no colour census could see' },"""


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
    raise SystemExit('PH-2 REFUSED: %s' % msg)


def fit(text, lit):
    """A multi-line anchor written LF here, converted to whatever THIS file
    mostly uses. PX-1's hazard, third round running. All five templates
    this round edits are CRLF and base.html is not, so an anchor written
    one way would refuse on five files or on one."""
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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, and it is asked of the TREE: if no page
    # still carries one of the old blocks, the markup half is done.
    live = 0
    for page, old, _new, _what in EDITS:
        live += read(alv_tree.path_of(page)).count(old)
    if not live:
        print('PH-2  already applied - no panel head still wears a status '
              'colour as chrome.')
        return 0

    out = {}
    pages = set()
    for page, old, new, what in EDITS:
        p = alv_tree.path_of(page)
        s = out.get(p, read(p))
        once(s, old, '%s (%s)' % (page, what))
        out[p] = s.replace(old, new, 1)
        pages.add(page)
    if len(pages) != N_PAGES:
        refuse('expected %d page(s); edited %d' % (N_PAGES, len(pages)))

    # ---------------------------------------------------------------- 1
    # base.html - the one declaration
    p = alv_tree.path_of(BASE)
    s = read(p)
    if '.bg-light {' in s:
        refuse('%s already owns .bg-light' % BASE)
    out[p] = swap(s, BASE_WAS, BASE_NOW, '%s (.bg-light)' % BASE)

    # --------------------------------------------------------------- 1b
    # the colour census, which comes DOWN by one
    p = os.path.join(root, CSS)
    s = read(p)
    s = swap(s, CSS_MARKUP_WAS, CSS_MARKUP_NOW, '%s (the inline count)' % CSS)
    s = swap(s, CSS_PAGES_WAS, CSS_PAGES_NOW, '%s (the page count)' % CSS)
    out[p] = s

    p = os.path.join(root, NEU)
    out[p] = swap(read(p), NEU_WAS, NEU_NOW, '%s (the cross-check)' % NEU)

    p = os.path.join(root, IMP)
    s = read(p)
    s = swap(s, IMP_BASE_WAS, IMP_BASE_NOW, '%s (base count)' % IMP)
    s = swap(s, IMP_TREE_WAS, IMP_TREE_NOW, '%s (tree count)' % IMP)
    out[p] = s

    p = os.path.join(root, VOC)
    s = read(p)
    if 'THE TOKEN, NOT THE ATTRIBUTE' in s:
        refuse('%s already repaired' % VOC)
    s = swap(s, VOC_RA_WAS, VOC_RA_NOW, '%s (the row-actions match)' % VOC)
    s = swap(s, VOC_CONV_WAS, VOC_CONV_NOW, '%s (CONVERTED)' % VOC)
    s = swap(s, VOC_ROUNDS_WAS, VOC_ROUNDS_NOW, '%s (ROUNDS)' % VOC)
    out[p] = s

    # ---------------------------------------------------------------- 2
    # the registers and the two counters these rounds keep by hand
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_panel_heads.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, CLAIMS_ANCHOR, CLAIMS, '%s (the claims)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'PH-2, 14 Oct 2026 - this round own suite. The panel '
                  'heads, after Demetri asked why three recipe screens '
                  'were green.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'PH-2, 14 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 3
    if CHECK:
        print('PH-2 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('PH-2 applied.')
    print('   %d panel head(s) on %d page(s) onto the house card'
          % (N_HEADS, N_PAGES))
    print('   the %d pantry chips leave their hex literal for '
          '--alv-good-soft' % 92)
    print('   .bg-light is house-owned - one declaration, zero pixels')
    print('   %d bg-* kept and named: the delete confirm, Make Now, '
          'Almost There' % N_KEPT)
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
