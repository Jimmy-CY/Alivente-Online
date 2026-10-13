# -*- coding: utf-8 -*-
"""apply_js_buttons.py - round E11, 13 Oct 2026.

A GATE THAT SAYS "NOTHING IS LEFT" MUST BE ASKED OF EVERYTHING.

E11 was logged as twenty buttons built inside <script>, sixteen of them
open. Measured today it is FIVE, on THREE pages, and the twenty were
never the thing that mattered.

WHERE THE OTHER FIFTEEN WENT
-----------------------------
Twenty-eight elements emitted from inside a <script> carry the exact
token `btn`. Twenty-three of them already wear a house tone - D2, D3,
the Financials segmented round and apply_row_actions took them one at a
time, each recording its own decision, and nobody went back to subtract
them from E11's twenty. Five are left:

    map_ingredients_nutrition.html  1452  Reload Queue         btn btn-info
    map_ingredients_nutrition.html  1461  Reload Queue         btn btn-info
    map_ingredients_nutrition.html  1462  Back to Ingredients  btn btn-secondary
    unit_conversions_wizard.html     747  Back to Ingredients  btn btn-info
    unit_conversions_management.html 1091 Save                 btn btn-sm btn-primary w-100

AND WHY NOBODY SAW THEM FOR SIX WEEKS
--------------------------------------
test_button_sweep.py section 10 asserts, in its own words:

    THE FINDING IS CLOSED, so this is no longer a floor - it is the
    statement that nothing is left.

Its corpus is `FILES = sb.templates(False)`, and templates() ends with
`if not include_recipes and is_recipe_side(rel): continue`. That is 117
of the application's 142 pages. All five sit in the other 25. Same
scanner, flag flipped:

    templates(False)   117 pages   len(_all) = 0   the claim is TRUE
    templates(True)    142 pages   len(_all) = 5   the claim is FALSE

A rule proved dead on a subset of its declarations is not a rule proved
dead. Third time in this instrument: E-10 (scan() could not open a CRS
page), X0 (walks_own_root only read scalars), this.

So the round is five class lists AND the corpus. Without the corpus the
next five are invisible again.

WHAT IT LOOKS LIKE - RENDERED, NOT READ OFF THE CLASS LISTS
------------------------------------------------------------
Bootstrap 4.1.3 + base.html + each page's own <style>, in the wrapper
the script really builds, with the inline style= it really writes:

    btn btn-info      teal rgb(14,124,139)  4.91   ->  action-primary   SAME COLOUR
    btn btn-secondary solid grey, white ink 4.69   ->  action-secondary teal outline
    btn btn-primary   BOOTSTRAP BLUE        3.98   ->  action-primary   teal 4.91

base.html recolours .btn-info to --alv-accent on purpose - its own
comment warns that moving the block above the Bootstrap link lets
Bootstrap win again - so THREE OF THE FIVE ARE ALREADY THE RIGHT
COLOUR. Those three are a naming defect, not a paint defect: the page
borrows the house colour through a Bootstrap class instead of owning it.

ONE IS A REAL CONTRAST FAILURE. .btn-primary is NOT overridden, so the
per-row Save on unit_conversions_management is Bootstrap blue with
white text at 3.98:1, under the 4.5 its 14px label wants.

AND ALL FIVE ARE 38px TALL ON A PHONE, AND ALL FIVE BECOME 44. Base's
min-height:44px mobile list names .btn.action-*; it does not name
.btn-info, .btn-secondary or .btn-primary. Reading the class lists would
never have shown that.

TWO DECISIONS DEMETRI TOOK, 13 OCT
-----------------------------------
1. The two Back-to-Ingredients buttons are NOT `action-back`, and they
   are not the same tone as each other. Rendered on their own cards:

                        label    own edge vs the white card
     btn-secondary      4.69     4.69      solid grey, as it is today
     btn-info           4.91     4.91      solid accent, as it is today
     action-secondary  12.95     1.24      white fill, --alv-line edge
     action-back        5.53      none     transparent, 14px/600, a link

   map_ingredients_nutrition takes `action-secondary`, because its OWN
   scoped branch already writes exactly that for its return button two
   lines away, and because it sits beside a Reload Queue that is the
   card's primary.

   unit_conversions_wizard takes `action-primary`, because its Back is
   the ONLY control on the success card - so by the house's own rule
   about a bar's lone verb, it IS that card's verb. The 1.24 edge is
   base's decided value for --alv-line on paper (B-2, 6 Oct: 1.30 ->
   1.24, "and that was the decision"), so it is house-standard rather
   than a defect - but a lone control whose boundary reads at 1.24 on a
   white card is the one place where that decision bites, and a solid
   teal at 4.91 on both counts is the better answer there.

   Demetri looked at the measured numbers before choosing, twice: once
   for the tone and once again after the render showed the edge.

2. The per-row Save goes to `action-primary` AND LOSES ITS INLINE
   HEIGHT. `style="height: 38px;"` beats base's 44px phone rule, so the
   class change alone would have fixed the colour and left the tap
   target. It is the only way to commit that row, so it is that row's
   verb.

WHAT THIS ROUND DOES NOT DO
----------------------------
It does NOT widen the markup sweep. FILES stays sb.templates(False).
test_button_sweep's walk rebuilds a pre-sweep tree from .bak_btnsweep
and the recipe side has no such backup; that narrowness is a stated
position on alv_tree.WAITING and it is untouched. The census gets its
own corpus, JS_FILES, and the held reason is re-derived to say which
number is which - E-10 did the same thing to the same entry when its
numbers moved.

It does NOT touch base.html. Every class and rule already exists.

It does NOT touch the three script-built modal headers. Base took their
rules on 24 Sep under the pages' own class names - ALV MODAL OVERLAY v1,
"base takes the RULES and the pages keep the NAMES" - and
test_modal_overlay.py RENDERS them and asserts "it is the SAME gradient
.alv-modal-head paints - one look". 106 passed, 0 failed today. MH-2's
note that they were a blind spot is true of the header GATE and wrong
about the paint.

It does NOT touch the four Bootstrap-toned buttons in
unit_conversions_management's MARKUP - three modal-footer Cancels and a
modal-footer Save. Those belong to the recipe/personal-side button
sweep, which is 57 drifting buttons and 13 undecided across 25 pages,
logged and priced separately. The suite asserts those four are left
byte-identical, because "I only touched the script ones" is a claim and
not a fact until something checks it.

THE SECOND INSTRUMENT FIX: \\bbtn\\b WAS NOT THE TOKEN btn
----------------------------------------------------------
A hyphen is not a word character, so BTN's `\\bbtn\\b` also matched

    icon-action-btn      the tail
    btn-trends           the head
    add-new-btn-link     the MIDDLE

Measured over all 142 pages: 433 elements matched on nothing but that,
on 59 pages, plus 36 inside <script>. Not one is a class base.html owns.

Nothing was wrong, and that is the part worth writing down. They are
dropped one function later by `if not boot and not has_house: continue`
in _scan, and the two that DO sit inside a confirmed bar are both
action-more-item, which skip_reason() names. The only thing between a
page-local icon-action-btn and rebuild() prepending `btn
action-secondary` to it was whether somebody put that button inside a
.page-action-buttons.

Priced before it was agreed: 706 scanner hits over the whole application
become 704, and exactly TWO pages change - asset_detail and
celebration_management, each losing a row that was already `skipped`
with a reason. bars() decides what a bar is from this same regex, so if
bar detection had moved, far more than two pages would differ. The two
suites that call the scanner directly pin invariants, not counts:
test_drift_root asks "no drift" with a floor of 500 hits, and
test_disabled_state asks "no drift" with a page-count floor. No pinned
count moves.

ALSO RECORDED, NOT FIXED
-------------------------
BTN's finditer does not overlap, so a control nested inside another
control is invisible to it. lease_timeline.html's responsive
btn-label-full / btn-label-short spans are the live example - eight of
them, swallowed by the outer button's match. They are labels today. The
blind spot is the same family and it is written into the suite rather
than left to be rediscovered.

See test_js_buttons.py.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_jsbtn'
SUITE = 'test_js_buttons.py'
DRIFT = 'Show-ButtonDrift.py'
SWEEP = 'test_button_sweep.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

# NO NARROW TEMPLATE ROOT HERE. X0's rule, and this round walked
# straight into it: a label goes back to a file through
# alv_tree.path_of(), which knows both roots, and not through a join
# onto a pages/templates constant that knows one. The first draft of
# this round's suite had FOURTEEN narrow joins in it - inside the
# round whose whole point is that a gate must be asked of everything -
# and test_waiting_down section 3 caught every one.
#
# ITS DETECTOR READS PROSE, THOUGH. walks_own_root() strips comments
# before it looks, with a comment above it saying CODE, NOT PROSE.
# The narrow-join detector beside it does not, so a comment that
# merely NAMES the shape is counted as the shape. Not fixed here -
# that is somebody else's control and a third instrument change this
# round did not agree to - which is why this note talks around the
# literal instead of quoting it.

# ---------------------------------------------------------------------------
# the five, as exact strings. Each one is asserted to appear EXACTLY ONCE
# in its own file before anything is written.
# ---------------------------------------------------------------------------
MAP = 'map_ingredients_nutrition.html'
WIZ = 'unit_conversions_wizard.html'
MGT = 'unit_conversions_management.html'

BUTTONS = (
    (MAP,
     'class="btn btn-info"><i class="fas fa-redo"></i> Reload Queue</a>',
     'class="btn action-primary"><i class="fas fa-redo"></i> '
     'Reload Queue</a>',
     'Reload Queue, the scoped branch'),
    (MAP,
     '<a href="?" class="btn btn-info" style="margin-right:10px;">',
     '<a href="?" class="btn action-primary" style="margin-right:10px;">',
     'Reload Queue, the unscoped branch'),
    (MAP,
     '<a href="{% url \'ingredient_base_units_management\' %}" '
     'class="btn btn-secondary">',
     '<a href="{% url \'ingredient_base_units_management\' %}" '
     'class="btn action-secondary">',
     'Back to Ingredients, beside a Reload Queue'),
    (WIZ,
     '<a href="{% url \'ingredient_base_units_management\' %}" '
     'class="btn btn-info">',
     '<a href="{% url \'ingredient_base_units_management\' %}" '
     'class="btn action-primary">',
     'Back to Ingredients, ALONE on the success card, so it is the '
     'card verb'),
    (MGT,
     '<button type="button" class="btn btn-sm btn-primary w-100" '
     'onclick="saveSingleMissingConversion(${index})" '
     'style="height: 38px;">',
     '<button type="button" class="btn btn-sm action-primary w-100" '
     'onclick="saveSingleMissingConversion(${index})">',
     'the per-row Save - tone AND the inline height'),
)

N_BUTTONS = 5
N_PAGES = 3
N_INLINE_HEIGHT = 1          # the one style="height: 38px;" that goes
MGT_MARKUP_BOOT = 4          # left alone, on purpose, and asserted

CENSUS_NARROW, CENSUS_WIDE = 117, 142
HITS_LOOSE, HITS_TIGHT = 706, 704
TAIL_MARKUP, TAIL_SCRIPT = 433, 36
TAIL_IN_REGION = 2

CEILING_WAS, CEILING_NOW = 38, 38
CONVERTED_WAS, CONVERTED_NOW = 71, 72
WAITING_WAS, WAITING_NOW = 2, 2
ALIAS_WAS, ALIAS_NOW = 53, 55

# ---------------------------------------------------------------------------
# Show-ButtonDrift.py
# ---------------------------------------------------------------------------
BTN_WAS = (
    "BTN = re.compile(r'<(a|button|span)\\b[^>]*class=\"([^\"]*(?:\\bbtn\\b|"
    "\\baction-'\n"
    "                 r'(?:primary|secondary|danger|back|add-new|btn-back)"
    "\\b|'\n"
    "                 r'\\bback-button\\b)[^\"]*)\"[^>]*>(.*?)</\\1>', re.S)")

BTN_NOW = (
    "# E11, 13 Oct 2026 - \\bbtn\\b WAS NOT THE TOKEN `btn`. A hyphen is not\n"
    "# a word character, so it also matched the btn ENDING icon-action-btn,\n"
    "# the btn OPENING btn-trends, and the btn in the MIDDLE of\n"
    "# add-new-btn-link. Measured over all 142 pages: 433 elements matched\n"
    "# on nothing but that, across 59 pages, and 36 more inside <script>.\n"
    "# Not one of them is a class base.html owns.\n"
    "#\n"
    "# NOTHING WAS WRONG, and that is the part worth writing down. They are\n"
    "# dropped one function later, by `if not boot and not has_house:\n"
    "# continue` in _scan, and the only two that DO sit inside a confirmed\n"
    "# bar are both action-more-item, which skip_reason() names. The one\n"
    "# thing between a page-local icon-action-btn and rebuild() prepending\n"
    "# `btn action-secondary` to it was whether somebody put that button\n"
    "# inside a .page-action-buttons.\n"
    "#\n"
    "# Priced before it was agreed: 706 scanner hits over the whole\n"
    "# application become 704, and exactly TWO pages change - asset_detail\n"
    "# and celebration_management, each losing a row that was already\n"
    "# `skipped` with a reason. bars() decides what a bar IS from this same\n"
    "# regex; had bar detection moved, far more than two pages would differ.\n"
    "#\n"
    "# NOT FIXED, AND RECORDED: finditer does not overlap, so a control\n"
    "# nested inside another control is invisible here. lease_timeline.html\n"
    "# writes btn-label-full / btn-label-short spans inside its nav buttons\n"
    "# and the outer match swallows all eight. They are labels today.\n"
    "BTN = re.compile(r'<(a|button|span)\\b[^>]*class=\"([^\"]*(?:"
    "(?<![-\\w])btn(?![-\\w])'\n"
    "                 r'|\\baction-'\n"
    "                 r'(?:primary|secondary|danger|back|add-new|btn-back)"
    "\\b|'\n"
    "                 r'\\bback-button\\b)[^\"]*)\"[^>]*>(.*?)</\\1>', re.S)")

CENSUS_WAS = (
    "    js_rows = []\n"
    "    for _f in files:\n"
    "        for _hit in js_buttons(read(resolve(_f))):\n"
    "            js_rows.append((_f,) + _hit)")

CENSUS_NOW = (
    "    # E11, 13 Oct 2026 - THE CENSUS IS NOT SCOPED BY THE FLAG.\n"
    "    # `files` is templates(recipes), so without --recipes this loop\n"
    "    # asked 117 of the application's 142 pages - and the five\n"
    "    # Bootstrap-toned script buttons left in this codebase were all on\n"
    "    # the other 25. The report said 0 in 0 and meant 0 in 0 OF A\n"
    "    # SUBSET. A markup sweep can have a scope, because rewriting is\n"
    "    # scoped work and the recipe side was deferred by name. A CENSUS\n"
    "    # cannot: it exists to say what is left, and it has to be asked of\n"
    "    # everything or it says nothing.\n"
    "    #\n"
    "    # templates(True) stays inside pages/templates - test_drift_root\n"
    "    # already asserts no crs/ page appears in it, so this widens the\n"
    "    # census and still does not reach the second root.\n"
    "    js_rows = []\n"
    "    for _f in templates(True):\n"
    "        for _hit in js_buttons(read(resolve(_f))):\n"
    "            js_rows.append((_f,) + _hit)")

SCOPE_WAS = (
    "    print('  scope: %s' % ('the whole application'\n"
    "                           if recipes else 'property management '\n"
    "                           '(--recipes adds the recipe/meal-plan "
    "side)'))")

SCOPE_NOW = (
    "    print('  scope: %s' % ('the whole application'\n"
    "                           if recipes else 'property management '\n"
    "                           '(--recipes adds the recipe/meal-plan "
    "side)'))\n"
    "    # The line above is the MARKUP scope and the flag still sets it.\n"
    "    # The census below has no scope, and saying so here is what stops\n"
    "    # the next reader taking one number for the other. [E11]\n"
    "    print('  the <script> census is always all %d page(s), whatever '\n"
    "          'this scope says' % len(templates(True)))")

# ---------------------------------------------------------------------------
# test_button_sweep.py - section 10's corpus, and the control that holds it
# ---------------------------------------------------------------------------
SWEEP_WAS = (
    "_js = {}\n"
    "for f in FILES:\n"
    "    hits = sb.js_buttons(load(os.path.join(TPL, f)))\n"
    "    if hits:\n"
    "        _js[f] = hits\n")

SWEEP_NOW = (
    "# E11, 13 Oct 2026 - THE CORPUS WAS THE FAULT, NOT THE SCANNER.\n"
    "#\n"
    "# FILES is sb.templates(False): 117 of the application's 142 pages,\n"
    "# with the recipe/meal-plan side excluded by name. The check below\n"
    "# says nothing is left - its own comment says so out loud - and it\n"
    "# said it over 117 pages while five Bootstrap-toned script buttons\n"
    "# sat on the other 25. Same scanner, flag flipped: len(_all) 0 -> 5.\n"
    "#\n"
    "# THE CENSUS GETS ITS OWN CORPUS, AND FILES IS NOT WIDENED. The\n"
    "# markup walk above rebuilds a pre-sweep tree from .bak_btnsweep and\n"
    "# the recipe side has no such backup - widening FILES would hand this\n"
    "# suite live text in place of a snapshot, which is the as_left_by\n"
    "# mistake with the roles reversed. That narrowness is a stated\n"
    "# position on alv_tree.WAITING and E11 leaves it exactly where it is.\n"
    "JS_FILES = sb.templates(True)\n"
    "_js = {}\n"
    "for f in JS_FILES:\n"
    "    hits = sb.js_buttons(load(os.path.join(TPL, f)))\n"
    "    if hits:\n"
    "        _js[f] = hits\n")

CLAIM_WAS = (
    "      len(_all) == 0 and len(_js) == 0 and len(_open) == 0)\n")

CLAIM_NOW = (
    "      len(_all) == 0 and len(_js) == 0 and len(_open) == 0)\n"
    "# E11's CONTROL, and the reason this round is not just five class\n"
    "# lists. The widening above is one identifier, and an identifier is\n"
    "# easy to put back. Without this check, the claim overhead can be\n"
    "# satisfied for ever by narrowing what it asks - which is precisely\n"
    "# how it came to be true over 117 pages and false over 142.\n"
    "#\n"
    "# check() in this suite takes a name and a boolean - no detail arm -\n"
    "# so the numbers go in the NAME, where they print either way.\n"
    "check('CONTROL: .. asked of all %d page(s), not the sweep scope of %d'\n"
    "      % (len(JS_FILES), len(FILES)),\n"
    "      len(JS_FILES) == len(sb.templates(True)) > len(FILES)\n"
    "      and bool([f for f in JS_FILES if sb.is_recipe_side(f)]))\n")

# ---------------------------------------------------------------------------
# alv_tree.py
# ---------------------------------------------------------------------------
CONV_WAS = ("    # F2b's own suite.\n"
            "    'test_surface_border.py',\n"
            "]")
CONV_NOW = ("    # F2b's own suite.\n"
            "    'test_surface_border.py',\n"
            "    # E11, 13 Oct 2026 - the script census gets an owner.\n"
            "    'test_js_buttons.py',\n"
            "]")

HELD_WAS = (
    "    'test_button_sweep.py':\n"
    "        'pages  narrow BY DESIGN - its walk rebuilds a pre-sweep '\n"
    "        'tree from .bak_btnsweep, so widening it would copy the '\n"
    "        'second template root into a tree the sweep never '\n"
    "        'covered. 117 in the tool census against 151 in the '\n"
    "        'tree, and that gap is a stated position. [reason '\n"
    "        'replaced E-10, 11 Oct 2026 - it said 120 and 146, and '\n"
    "        'both numbers had moved]',")

HELD_NOW = (
    "    'test_button_sweep.py':\n"
    "        'pages  narrow BY DESIGN - its MARKUP walk rebuilds a '\n"
    "        'pre-sweep tree from .bak_btnsweep, so widening it would '\n"
    "        'copy the second template root into a tree the sweep never '\n"
    "        'covered. 117 in the markup scope against 151 in the '\n"
    "        'tree, and that gap is a stated position. Its <script> '\n"
    "        'census is NOT narrow: E11 gave that its own corpus of 142 '\n"
    "        'pages, because a census that reports what is LEFT cannot '\n"
    "        'have a scope. [reason replaced E11, 13 Oct 2026 - the 117 '\n"
    "        'has not moved, but it was called the tool census and there '\n"
    "        'are now two censuses with two numbers. Replaced E-10, 11 '\n"
    "        'Oct 2026 - it said 120 and 146, and both numbers had "
    "moved]',")


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
    raise SystemExit('E11 REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:70], n))


def bump(text, lit, was, now, note, where):
    """A pinned COUNT moves; the house convention keeps the old one in a
    trailing comment so the history reads back."""
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    def path(*parts):
        return os.path.join(root, *parts)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, before a single anchor is looked for,
    # and it is asked of the TREE rather than of a count: if no page
    # still holds one of the five old class lists, the round is done.
    live = sum(read(alv_tree.path_of(pg)).count(was)
               for pg, was, _now, _what in BUTTONS)
    if not live:
        print('E11  already applied - no script-built button wears a '
              'Bootstrap tone.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # the five class lists
    n_btn, pages = 0, set()
    for pg, was, now, what in BUTTONS:
        p = alv_tree.path_of(pg)
        s = out.get(p, read(p))
        once(s, was, '%s (%s)' % (pg, what))
        out[p] = s.replace(was, now, 1)
        n_btn += 1
        pages.add(pg)

    if n_btn != N_BUTTONS or len(pages) != N_PAGES:
        refuse('expected %d button(s) on %d page(s), planned %d on %d'
               % (N_BUTTONS, N_PAGES, n_btn, len(pages)))

    # the inline height is gone, and it is gone exactly once
    mgt_before = read(alv_tree.path_of(MGT))
    mgt_after = out[alv_tree.path_of(MGT)]
    lost = (mgt_before.count('style="height: 38px;"')
            - mgt_after.count('style="height: 38px;"'))
    if lost != N_INLINE_HEIGHT:
        refuse('the inline height: expected %d removed, got %d'
               % (N_INLINE_HEIGHT, lost))

    # AND THE FOUR IN THAT PAGE'S MARKUP ARE UNTOUCHED. Three
    # modal-footer Cancels and a modal-footer Save, all Bootstrap-toned,
    # all belonging to the recipe-side sweep and not to this round.
    for tone in ('btn btn-secondary', 'btn btn-primary'):
        if mgt_before.count(tone) != mgt_after.count(tone):
            refuse('%s: the markup tone %r moved, and this round claims '
                   'it does not touch markup' % (MGT, tone))
    n_markup = (mgt_after.count('class="btn btn-secondary"')
                + mgt_after.count('class="btn btn-primary"'))
    if n_markup != MGT_MARKUP_BOOT:
        refuse('%s: expected %d Bootstrap-toned button(s) left in markup, '
               'found %d' % (MGT, MGT_MARKUP_BOOT, n_markup))

    # ---------------------------------------------------------------- 2
    # the instrument: the regex, the corpus, and the line that says
    # which is which
    p = path(DRIFT)
    s = read(p)
    for was, now, what in ((BTN_WAS, BTN_NOW, 'BTN'),
                           (CENSUS_WAS, CENSUS_NOW, 'the census corpus'),
                           (SCOPE_WAS, SCOPE_NOW, 'the scope line')):
        once(s, was, '%s (%s)' % (DRIFT, what))
        s = s.replace(was, now, 1)
    out[p] = s

    # ---------------------------------------------------------------- 3
    # the suite whose claim this round is really about
    p = path(SWEEP)
    s = read(p)
    for was, now, what in ((SWEEP_WAS, SWEEP_NOW, 'section 10 corpus'),
                           (CLAIM_WAS, CLAIM_NOW, "the claim's control")):
        once(s, was, '%s (%s)' % (SWEEP, what))
        s = s.replace(was, now, 1)
    out[p] = s

    # ---------------------------------------------------------------- 4
    # the registers
    p = path(TREE)
    s = read(p)
    for was, now, what in ((CONV_WAS, CONV_NOW, 'CONVERTED'),
                           (HELD_WAS, HELD_NOW, 'the held reason')):
        once(s, was, '%s (%s)' % (TREE, what))
        s = s.replace(was, now, 1)
    out[p] = s

    p = path(ROUNDS)
    s = read(p)
    anchor = "    '.bak_surfborder',\n]"
    once(s, anchor, '%s (ROUNDS)' % ROUNDS)
    out[p] = s.replace(anchor, "    '.bak_surfborder',\n    '%s',\n]"
                       % SUFFIX, 1)

    p = path(WD)
    s = read(p)
    out[p] = bump(s, 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'E11, 13 Oct 2026 - this round own suite. '
                  'test_button_sweep is NOT released: its markup walk is '
                  'narrow by design and E11 widened only its census.',
                  '%s (CONVERTED_N)' % WD)

    p = path(CO)
    s = read(p)
    old = "ok(len(aliased) == %d," % ALIAS_WAS
    once(s, old, '%s (alias count)' % CO)
    s = s.replace(old, "ok(len(aliased) == %d," % ALIAS_NOW, 1)
    # The %d in that line is LITERAL source, not this patcher's format
    # slot - the count it prints is len(aliased), read live. What moves is
    # the prose split, 26/27 -> 27/28, which is a pinned DECISION about
    # what the files are rather than a count of them.
    old2 = ("'%d file(s) alias it - 26 patchers and 27 suites' "
            "% len(aliased),")
    once(s, old2, '%s (alias wording)' % CO)
    s = s.replace(old2,
                  ("'%d file(s) alias it - 27 patchers and 28 suites' "
                   "% len(aliased),   # E11, 13 Oct 2026 - this round own "
                   "patcher and suite   # (was " + str(ALIAS_WAS)
                   + ", 26 and 27)"), 1)
    out[p] = s

    p = path(PS1)
    s = read(p)
    anchor = "    'test_surface_border.py'\n)"
    once(s, anchor, '%s ($suites)' % PS1)
    out[p] = s.replace(anchor,
                       "    'test_surface_border.py',\n    '%s'\n)" % SUITE, 1)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('E11  --check: %d file(s) would change' % len(out))
        for q in sorted(out):
            print('        %s' % os.path.relpath(q, root))
        print('      %d button(s) on %d page(s); the inline 38px goes; '
              '%d Bootstrap-toned button(s) stay in %s markup'
              % (N_BUTTONS, N_PAGES, MGT_MARKUP_BOOT, MGT))
        print('      census %d -> %d pages; BTN hits %d -> %d'
              % (CENSUS_NARROW, CENSUS_WIDE, HITS_LOOSE, HITS_TIGHT))
        print('      CONVERTED %d -> %d; WAITING %d -> %d; ceiling %d; '
              'aliases %d -> %d'
              % (CONVERTED_WAS, CONVERTED_NOW, WAITING_WAS, WAITING_NOW,
                 CEILING_NOW, ALIAS_WAS, ALIAS_NOW))
        return 0

    for q in sorted(out):
        backup(q)
        write(q, out[q])
    print('E11  applied to %d file(s).' % len(out))
    print('     %d script-built button(s) on %d page(s) onto house tones.'
          % (N_BUTTONS, N_PAGES))
    print('     The <script> census now asks all %d page(s), not %d.'
          % (CENSUS_WIDE, CENSUS_NARROW))
    print('     BTN matches the TOKEN btn: %d hits -> %d, two skipped rows.'
          % (HITS_LOOSE, HITS_TIGHT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
