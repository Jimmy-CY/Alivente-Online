# -*- coding: utf-8 -*-
"""apply_verb_colours.py - round VB-1, 15 Oct 2026.

A COLOUR THAT NAMES A VERB IN ONE MODULE AND A DIFFERENT VERB IN ANOTHER
NAMES NOTHING.

Demetri, on the live site, in three separate messages:

  "Why is my selection 'Chicken' Green as well as the hover overs, also
   green? For the Ingredients, why are my selection, and the hover over,
   green?"

  "When I go to Map the Nutritional data of a new ingredient, the
   confirmation bar at the bottom cannot be read clearly... It seems
   brown on brown."

  "Why is the Edit Button this colour, but in other modules it is Blue?"

Three questions, one answer, in three places. base.html already owns a
vocabulary for all of them:

    --alv-accent / -soft   the BRAND, and base's own comment on the soft
                           token reads "tint: hover rows, selected chips"
    --alv-good             a POSITIVE STATUS
    --alv-edit  #2563eb    the verb CHANGE
    --alv-view  = accent   the verb LOOK
    --alv-danger = bad     the verb DESTROY
    --alv-*-line           the tint's edge, AND pale on a dark ground

Every control this round touches was already reachable from that list and
was reaching somewhere else instead.

NAMED VB-1. Checked: the string appears in no file in this repo.


ONE: THE CHIPS ARE A SELECTION, AND A SELECTION IS NOT A STATUS
----------------------------------------------------------------
PH-2 took the status green off the panel HEADS the day before. The chips
underneath still wore it:

    wcim_landing  .anchor-btn:hover     --alv-good-soft
                  .anchor-btn.selected  --alv-good
    wcim_extras   .extra-btn:hover      --alv-good-soft
                  .extra-btn.selected   --alv-good

Picking Chicken is not good news. It is a choice. And base answers this
in writing, on the token itself:

    --alv-accent-soft: #e4f3f5;   /* tint: hover rows, selected chips */

These were the only chips in the application that disagreed with that
comment.

    AND A LITERAL NO CENSUS COULD SEE. .anchor-btn.selected also carried
    box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3) - BOOTSTRAP's green, as
    an rgba triple. Not a hex, so no hex census ever counted it; not a
    token, so no token census either. Same shape as the 92 pantry chips
    PH-2 found sitting in an inline style. It moves to the accent triple.


TWO: THE TOAST WAS NOT BROKEN. A ROUND BROKE IT.
-------------------------------------------------
This is the part worth reading twice.

apply_amber.py (B-4) listed the Undo button as one of its three real
defects, in its own docstring:

    "amber used as TEXT: .toast-undo-btn at 1.63:1"

1.63 is amber on WHITE PAPER. The toast's ground is not paper - the rule
four declarations up reads `background: var(--alv-ink)`. Measured against
the surface the control actually sits on:

    amber #ffc107        on the toast    7.95:1      it PASSED
    --alv-warn-ink       on the toast    1.60:1      B-4's "fix"
    --alv-warn-line      on the toast    8.87:1      this round

B-4 took a passing control to failing and counted it among its nine
fixes. Not carelessness - it measured against paper because paper is what
the census knows. The tick beside it is the same mistake untouched:
--alv-good on the toast reads 2.53:1, under even the 3:1 floor a
non-text glyph is held to.

    AND test_amber COULD NOT CATCH IT. Section 4's check is

        ok('var(--alv-warn' in now, '... now reads a warn token')

    which asserts the rule NAMES a warn token. It passes at 8.87 and it
    passes at 1.60. A check that cannot fail for the reason it exists.
    This round rewrites it to resolve the rule's REAL ground - the
    ancestor that paints one - and measure. See section 4 of the suite.

    THE CAUSE IS GENERAL, SO IT WAS COUNTED. The rule sets
    `background: transparent`; its ground belongs to the ancestor. No
    census in this project chases an ancestor. RC-2 left the mirror image
    open in writing - "the pair census still cannot pair a fill with an
    inherited text colour... nobody has counted how many others exist
    tree-wide". Nobody had counted the inherited GROUNDS either. There
    are 14 below AA. This round fixes the 2 in the toast and NAMES the
    other 12 rather than leaving them to be rediscovered; 4 of those 12
    are the accent-on-tint base decision still waiting on Demetri, and
    pre-empting it here is exactly what RC-2 refused to do.

    AND NO NEW TOKEN. My first proposal was to add one. The good family
    already has four members - good, -soft, -ink, -line - and I had read
    a truncated grep that showed two. --alv-good-line is #bfe0cd and
    reads 9.10:1 on the toast, BETTER than the token I was about to mint.
    Second count of mine this week taken off a short read.


THREE: THE RECIPE OVERLAY IS A PRIVATE VOCABULARY THE GATE CANNOT SEE
----------------------------------------------------------------------
Every other module draws a row action as `icon-action-btn icon-edit` -
outlined, --alv-edit blue. recipe_management has its own quartet, filled
32px circles, defined on that page and used nowhere else:

    .recipe-view-btn       --alv-good     green   house says teal
    .recipe-edit-btn       --alv-spice    sienna  house says blue
    .recipe-duplicate-btn  --alv-accent   teal    house says blue
    .recipe-delete-btn     --alv-bad      red     matches

One of four. And two of the three are not merely different - they wear
colours the house has given to OTHER verbs. View is on the positive
status token. Duplicate is on --alv-accent, which IS --alv-view: the
Copy button wears the View colour, next to a View button that does not.

    WHY THE PENCIL IS SIENNA. RC-2 put it there on 9 Oct and it was a
    RESCUE, not a choice about Edit: that button was #ffc107 with white
    text at 1.63:1, invisible. RC-2 moved it to --alv-spice at 5.82:1
    under its rule "warm is the module's identity". It fixed the contrast
    inside the page's own vocabulary. It never asked whether that
    vocabulary should exist. Demetri was asked and it should not.

    THE CONVERSION WIZARD KEEPS ITS SPICE. Asked separately the same
    afternoon and re-affirmed: RC-2 chose spice there on MEANING, and a
    decided decision does not move because a later round finds it
    convenient. This round takes two declarations out of RC-2's 28 and
    leaves the other 26 alone.

    CONTRAST IS NOT THE ARGUMENT HERE. White reads 5.82 on spice, 5.12 on
    good, 4.91 on accent, 6.54 on bad and 5.17 on edit. All five pass.
    This is vocabulary, and the suite says so rather than implying a
    defect that is not there.

    .recipe-delete-btn MOVES AND NO PIXEL DOES. --alv-danger IS
    var(--alv-bad). Identical value, so this changes nothing on screen
    and everything about ownership - the same move PH-2 made for
    .bg-light the day before.

    DUPLICATE LOSES A HOVER COLOUR AND GAINS ITS SIBLINGS'. It was the
    only one of the four with a darkening hover (--alv-accent-ink, twice:
    grid and list). --alv-edit has no -ink partner, and rather than mint
    one for a single hover on a single page, the two rules go and all
    four controls behave identically - scale(1.1), which is what View,
    Edit and Delete already did. Demetri decided it.

THE FOUR ARE REGISTERED, WHICH IS THE DURABLE HALF
----------------------------------------------------
Run Show-ButtonDrift against recipe_management and it finds 13 buttons -
the top bar, the modals - and NOT ONE of the four overlay controls. They
carry no `icon-action-btn`, so the row-action guard has never seen them.
That is how four controls sat three-quarters wrong for weeks with every
gate green, and fixing the colours without fixing that would leave the
next person no warning.

alv_rowactions.py gains VERNACULAR: a register of page-local action
vocabularies, mapping a private class onto the house verb it means. The
module already exists to write the order down ONCE for three callers;
this writes the TRANSLATION down once, in the same place, and the suite
reads it for both the colour and the FAMILY order.

WHAT THIS ROUND DOES NOT TOUCH
--------------------------------
  the conversion wizard's spice    re-affirmed, above
  the other 12 ancestor grounds    named in the suite, decided later
  the cookbook theme               RC-2's 22 declarations, untouched
  --alv-edit has no -ink           not minted for one hover

See test_verb_colours.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_verbs'
SUITE = 'test_verb_colours.py'
BASE = 'base.html'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
RA = 'alv_rowactions.py'
AMBER = 'test_amber.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

N_DECLS = 21        # repointed colour declarations across 5 pages
N_PAGES = 5
N_DROPPED = 2       # the two duplicate hover rules
N_CONTROLS = 4      # the registered overlay quartet
# ancestor-ground pairs below AA, tree-wide. MY FIRST COUNT WAS 14 and
# it was low: the probe that produced it read rules with a regex of its
# own, and that regex could not see inside an @media block. Counted
# through alv_cssrules, which can: 22, of which this round fixes 3.
N_ANCESTOR = 22
N_ANCESTOR_FIXED = 3

CONVERTED_WAS, CONVERTED_NOW = 77, 78
ALIAS_WAS, ALIAS_NOW = 65, 67
ALIAS_P_WAS, ALIAS_P_NOW = 32, 33
ALIAS_S_WAS, ALIAS_S_NOW = 33, 34

# ---------------------------------------------------------------------------
# THE MARKUP. Each entry is (page, old, new, what), and `old` is matched
# EXACTLY ONCE or the round refuses. Multi-line anchors are written LF here
# and fitted to the file's own majority ending by fit() - these five pages
# are not all the same, which is PX-1's hazard and the reason fit exists.
# ---------------------------------------------------------------------------
EDITS = [
    # ---- the chooser chips ------------------------------------------- 1
    ('wcim_landing.html',
     """  .anchor-btn:hover {
    border-color: var(--alv-good);
    background: var(--alv-good-soft);
  }
  .anchor-btn.selected {
    background: var(--alv-good);
    color: var(--alv-on-accent);
    border-color: var(--alv-good);
    box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);
  }""",
     """  .anchor-btn:hover {
    border-color: var(--alv-accent);
    background: var(--alv-accent-soft);
  }
  .anchor-btn.selected {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    border-color: var(--alv-accent);
    /* VB-1: was rgba(40, 167, 69, 0.3) - BOOTSTRAP's green, as an rgba
       triple. Not a hex and not a token, so no census in this project
       could see it. The accent triple is #0e7c8b. */
    box-shadow: 0 2px 6px rgba(14, 124, 139, 0.3);
  }""",
     'the chooser chip, hover and selected, and the rgba literal'),

    # ---- the ingredient chips ---------------------------------------- 2
    ('wcim_extras.html',
     """  .extra-btn:hover {
    border-color: var(--alv-good);
    background: var(--alv-good-soft);
  }
  .extra-btn.selected {
    background: var(--alv-good);
    color: var(--alv-on-accent);
    border-color: var(--alv-good);
  }""",
     """  .extra-btn:hover {
    border-color: var(--alv-accent);
    background: var(--alv-accent-soft);
  }
  .extra-btn.selected {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    border-color: var(--alv-accent);
  }""",
     'the ingredient chip, hover and selected'),
]

# ---- the toast ---------------------------------------------------------- 3
# THE TWO PAGES DO NOT CARRY THE SAME TOAST, and I told Demetri they did.
# Both have `.undo-toast` and both have the tick. Only
# map_ingredients_nutrition has an Undo BUTTON - the wizard's toast is a
# plain confirmation, `<i class="fas fa-check-circle toast-icon"></i>` and
# "Saved <strong>name</strong>", with nothing to press.
#
# Which makes his report exactly right and my reading of it wrong. He
# wrote "It seems brown on brown. The same applies to the Unit
# Conversions." What is wrong on the wizard is the TICK at 2.53:1, not an
# Undo at 1.60:1, and had this round trusted my sentence instead of the
# file it would have refused on an anchor that was never there. It did.
TOAST_PAGES = ('map_ingredients_nutrition.html',
               'unit_conversions_wizard.html')
TOAST_BTN_PAGES = ('map_ingredients_nutrition.html',)

TOAST_ICON_WAS = """.undo-toast .toast-icon {
    color: var(--alv-good);"""
TOAST_ICON_NOW = """.undo-toast .toast-icon {
    /* VB-1: was var(--alv-good) - 2.53:1 on this toast, under even the
       3:1 a non-text glyph is held to. --alv-good is a status token for
       a LIGHT surface. --alv-good-line reads 9.10:1 here, and base
       calls the -line tokens pale-on-dark-ink in its own words. */
    color: var(--alv-good-line);"""

TOAST_BTN_WAS = """    background: transparent;
    color: var(--alv-warn-ink);"""
TOAST_BTN_NOW = """    background: transparent;
    /* VB-1: was var(--alv-warn-ink) - 1.60:1 on this toast. B-4 put it
       here measuring amber against WHITE PAPER (1.63:1) when the ground
       four declarations up is var(--alv-ink): the control read 7.95:1
       before that round and 1.60:1 after. --alv-warn-line reads 8.87:1,
       and is already the border on the next line - which is exactly why
       the outline was visible and the word was not. */
    color: var(--alv-warn-line);"""

# ---- the recipe overlay ------------------------------------------------- 4
RM = 'recipe_management.html'

RM_EDITS = [
    # THE THREE DESKTOP RULES ARE TAKEN AS ONE BLOCK, anchored on the
    # :hover line above them. Alone, `.recipe-view-btn { ... }` matches
    # TWICE - the phone rule four hundred lines down ends with the same
    # text, `.recipe-card-actions-mobile .recipe-view-btn { ... }`. The
    # gate caught it; a patcher that took the first match would have
    # written the desktop rule and left the phone one, which is the
    # failure mode every one of these rounds exists to make impossible.
    (""".recipe-image-action-btn:hover { transform: scale(1.1); }
.recipe-view-btn { background: var(--alv-good); color: var(--alv-on-accent); }
.recipe-edit-btn { background: var(--alv-spice); color: var(--alv-on-accent); }
.recipe-delete-btn { background: var(--alv-bad); color: var(--alv-on-accent); }""",
     """/* VB-1, 15 Oct 2026 - THE VERBS, NOT THE MODULE.
   Demetri: "Why is the Edit Button this colour, but in other modules it
   is Blue?" Because these four were a private vocabulary: View on the
   positive-status token, Edit on the recipe module's spice, Duplicate on
   --alv-accent - which IS --alv-view, so Copy was wearing View's colour -
   and only Delete agreeing with the house.

   The shape stays. They are filled circles because they sit on a
   photograph and an outlined row action does not read there; Demetri
   chose to keep that and give up only the private meanings.

   Contrast was never the argument: white reads 5.82 on spice, 5.12 on
   good, 4.91 on accent and 5.17 on edit. All of them pass. This is
   vocabulary. --alv-danger IS var(--alv-bad), so Delete moves name only
   and no pixel at all. */
.recipe-image-action-btn:hover { transform: scale(1.1); }
.recipe-view-btn { background: var(--alv-view); color: var(--alv-on-accent); }
.recipe-edit-btn { background: var(--alv-edit); color: var(--alv-on-accent); }
.recipe-delete-btn { background: var(--alv-danger); color: var(--alv-on-accent); }""",
     'View, Edit and Delete onto LOOK, CHANGE and DESTROY'),
    ("""/* Duplicate button styling */
.recipe-duplicate-btn { background-color: var(--alv-accent); color: var(--alv-on-accent); }
.recipe-duplicate-btn:hover { background-color: var(--alv-accent-ink); }
.recipe-list-action-btn.recipe-duplicate-btn { background-color: var(--alv-accent); }
.recipe-list-action-btn.recipe-duplicate-btn:hover { background-color: var(--alv-accent-ink); }""",
     """/* Duplicate button styling - VB-1, 15 Oct 2026.
   WAS var(--alv-accent), which IS var(--alv-view): the Copy button was
   wearing the View colour, next to a View button that was not. The house
   gives COPY the same token as CHANGE - base's own .icon-duplicate reads
   var(--alv-edit) - so Duplicate and Edit share a colour here too and are
   told apart by their glyph, exactly as they are everywhere else.

   AND THE HOVER COLOUR GOES. This was the only one of the four with a
   darkening hover. --alv-edit has no -ink partner, and minting one for a
   single hover on a single page is worse than letting all four controls
   behave the same way: scale(1.1), which is what the other three already
   did. Demetri decided it. */
.recipe-duplicate-btn { background-color: var(--alv-edit); color: var(--alv-on-accent); }
.recipe-list-action-btn.recipe-duplicate-btn { background-color: var(--alv-edit); }""",
     'Duplicate, onto the CHANGE token, and two hover rules dropped'),
    ('    .recipe-card-actions-mobile .recipe-view-btn { background: '
     'var(--alv-good); color: var(--alv-on-accent); }\n'
     '    .recipe-card-actions-mobile .recipe-edit-btn { background: '
     'var(--alv-spice); color: var(--alv-on-accent); }\n'
     '    .recipe-card-actions-mobile .recipe-duplicate-btn { background: '
     'var(--alv-accent); color: var(--alv-on-accent); }\n'
     '    .recipe-card-actions-mobile .recipe-delete-btn { background: '
     'var(--alv-bad); color: var(--alv-on-accent); }',
     '    /* VB-1: the same four verbs, on the phone. Every Add/Edit screen\n'
     '       in this application has to work on a phone, so a vocabulary\n'
     '       fixed only at 1180 is fixed nowhere. */\n'
     '    .recipe-card-actions-mobile .recipe-view-btn { background: '
     'var(--alv-view); color: var(--alv-on-accent); }\n'
     '    .recipe-card-actions-mobile .recipe-edit-btn { background: '
     'var(--alv-edit); color: var(--alv-on-accent); }\n'
     '    .recipe-card-actions-mobile .recipe-duplicate-btn { background: '
     'var(--alv-edit); color: var(--alv-on-accent); }\n'
     '    .recipe-card-actions-mobile .recipe-delete-btn { background: '
     'var(--alv-danger); color: var(--alv-on-accent); }',
     'the same four verbs at 390px'),
]

# ---------------------------------------------------------------------------
# base.html - TWO COMMENTS AND NOT ONE DECLARATION
# ---------------------------------------------------------------------------
# The reason this round nearly minted a token that already existed is that
# only ONE of the three -line tokens says what it is for on a dark ground:
#
#   --alv-good-line   /* the tint's own edge              */
#   --alv-warn-line   /* the tint's own edge              */
#   --alv-spice-line  /* edges, and pale warm on dark ink */   <- only this
#
# Both of the first two are exactly that, measured: 9.10:1 and 8.87:1 on
# --alv-ink. Two comments, no value changes, and the next person reaching
# for a pale warm or green on a dark surface finds the token instead of
# minting a fourth. The column width is held so nothing else moves.
BASE_EDITS = [
    ("        --alv-good-line:  #bfe0cd;   /* the tint's own edge              */",
     "        --alv-good-line:  #bfe0cd;   /* edge, and pale green on dark ink */",
     'good-line says what it is for'),
    ("        --alv-warn-line:  #ecd39e;   /* the tint's own edge              */",
     "        --alv-warn-line:  #ecd39e;   /* edge, and pale warm on dark ink  */",
     'warn-line says what it is for'),
]

# ---------------------------------------------------------------------------
# alv_rowactions.py - VERNACULAR
# ---------------------------------------------------------------------------
RA_WAS = """    },
}


def named(page, hits):"""

RA_NOW = '''    },
}


# A PAGE-LOCAL VOCABULARY, TRANSLATED ONCE.            [VB-1, 15 Oct 2026]
#
# Demetri: "Why is the Edit Button this colour, but in other modules it is
# Blue?" Because recipe_management does not draw its row actions the way
# the rest of the application does. They are filled 32px circles in three
# wrappers - the card overlay, the phone bar, the list row - and they
# carry no `icon-action-btn`, so NOTHING in this project could see them.
# Show-ButtonDrift finds 13 buttons on that page and not one of these
# four. That is how a quartet sat three-quarters wrong with every gate
# green, and it is why the colours alone were not the fix.
#
# This is the same bargain the module already strikes for the ORDER: the
# rule is written down ONCE, here, rather than three times in three
# callers. VERNACULAR writes down the TRANSLATION - private class to house
# verb - and the verb is then enough to say both what colour it must wear
# and where it must sit in the row.
#
# A PAGE EARNS AN ENTRY BY BEING LOOKED AT, NOT BY BEING FOUND. Adding one
# is a decision that a page may keep its own shape. recipe_management kept
# its filled circles because they sit on a photograph and an outlined
# control does not read there - Demetri chose that over moving the markup
# onto .icon-action-btn. What it did not get to keep is its own meaning
# for a colour.
VERNACULAR = {
    'recipe_management.html': {
        'since': '.bak_verbs',
        'wrappers': ('recipe-image-actions', 'recipe-card-actions-mobile',
                     'recipe-list-actions'),
        # private class -> the house verb it means. The verb decides the
        # token through TONE below, and the FAMILY order above.
        'controls': (('recipe-view-btn', 'view'),
                     ('recipe-edit-btn', 'edit'),
                     ('recipe-duplicate-btn', 'duplicate'),
                     ('recipe-delete-btn', 'delete')),
        'why': 'The recipe card overlay. Filled circles on a photograph '
               'rather than outlined row actions, which Demetri kept - '
               'but on the house verb tokens, which it did not have.',
    },
}

# The verb decides the colour. These are base.html's names, not values:
# --alv-view is var(--alv-accent) and --alv-danger is var(--alv-bad), and
# a register that held the VALUES would stop being true the day a token is
# tuned. COPY shares CHANGE's token because base's own .icon-duplicate
# does - the two are told apart by their glyph, not their colour.
TONE = {
    'view': '--alv-view',
    'edit': '--alv-edit',
    'duplicate': '--alv-edit',
    'delete': '--alv-danger',
}


def vernacular(page):
    """The page's private action vocabulary, or None."""
    return VERNACULAR.get(page)


def tone_of(verb):
    """The house token a verb must wear, or None if the verb has no
    settled colour. Not every FAMILY member does: ADVANCE covers send,
    approve, void and lock, and those are not one colour."""
    return TONE.get(verb)


def named(page, hits):'''

# ---------------------------------------------------------------------------
# test_amber.py - A CHECK THAT COULD NOT FAIL FOR THE REASON IT EXISTS
# ---------------------------------------------------------------------------
# RC-2 set the precedent when it re-pointed this same suite: "A pinned COUNT
# moves when a later round owns part of it. A pinned DECISION does not move
# because a later round finds it inconvenient." This is neither - it is a
# pinned check that was never measuring what its own sentence claimed.
AMBER_WAS = """for pg, tail in FIXED:
    path = T.path_of(pg)
    if not path:
        skip(pg, 'not in this tree')
        continue
    now = rule(path, tail) or ''
    ok('var(--alv-warn' in now,
       '%-30s %s now reads a warn token' % (pg, tail), now[:90])"""

AMBER_NOW = '''# --------------------------------------------------- VB-1, 15 Oct 2026
# THIS CHECK USED TO READ
#
#     ok('var(--alv-warn' in now, '... now reads a warn token')
#
# which asserts the rule NAMES a warn token. It passes at 8.87:1 and it
# passes at 1.60:1, and .undo-toast .toast-undo-btn was sitting at 1.60
# for six days underneath it.
#
# B-4 moved that control here measuring amber against WHITE PAPER - the
# 1.63 in this suite's own FIXED table. The toast's ground is not paper;
# `.undo-toast` sets background: var(--alv-ink) four declarations up, and
# the button sets `background: transparent`, so its ground belongs to its
# ANCESTOR. Against the real ground the control read 7.95:1 BEFORE this
# round touched it and 1.60:1 after. B-4 did not lower a passing control
# through carelessness; it measured against paper because paper is what
# the census knows.
#
# So the check now resolves the ground the way a browser does - nearest
# ancestor that paints one, paper if none - and MEASURES. It fails if any
# of these three ever drops below AA again, for any reason, including a
# future round swapping one warn token for another.
for pg, tail in FIXED:
    path = T.path_of(pg)
    if not path:
        skip(pg, 'not in this tree')
        continue
    now = rule(path, tail) or ''
    ok('var(--alv-warn' in now,
       '%-30s %s now reads a warn token' % (pg, tail), now[:90])
    ink, ground, where = _on_its_real_ground(path, tail)
    if ink is None or ground is None:
        skip('%s %s' % (pg, tail), 'the pair does not resolve to two hexes')
        continue
    c = B.contrast(ink, ground)
    ok(c >= 4.5,
       '  and reads %.2f:1 on %s, which is the ground it SITS on'
       % (c, where), '%s on %s' % (ink, ground))'''

AMBER_HELPER_ANCHOR = """# ==========================================================================
head('4. THE INK - AND WHAT HE CHOSE KNOWING THE COST')
# ==========================================================================\
"""

AMBER_HELPER = '''def _value(code, ba, bb, prop):
    d = R.decl_span(code, ba, bb, prop)
    if d is None:
        return None
    return R.norm(code[d[0]:d[1]].partition(':')[2]).rstrip(';').strip()


def _on_its_real_ground(path, tail):
    """(ink, ground, where) for a rule, resolving its ground the way a
    BROWSER does rather than the way a pair census does.

    A rule that sets no background of its own - or sets `transparent` -
    does not sit on paper. It sits on whatever its nearest ANCESTOR
    paints. VB-1 added this because this suite had been asserting a token
    NAME where it meant to assert a ratio, and the one control it most
    wanted to protect was sitting at 1.60:1 underneath it.

    It reads through alv_cssrules and apply_edit_ink rather than a fourth
    regex of its own. RC-2 counted eight occasions in one week where a
    count of mine fired on prose because it was read with a pattern
    instead of with the instrument that already existed.
    """
    # Imported here and not at the top: this helper is the only caller,
    # and B (apply_amber) owns contrast while EI owns the token chase.
    import apply_edit_ink as EI
    code = T.code_only(read(path))
    tok = EI.base_tokens()
    want = tail.strip()
    grounds, own_bg, ink = {}, None, None
    for a, b in R.style_spans(code):
        for sel, ba, bb, _r, _s in R.rule_spans(code, a, b):
            name = sel.split(' && ')[-1].strip()
            bg = _value(code, ba, bb, 'background')
            if bg is None:
                bg = _value(code, ba, bb, 'background-color')
            if bg is not None:
                grounds.setdefault(name.split(':')[0].strip(),
                                   bg.split()[0])
            if name != want:
                continue
            if bg is not None:
                own_bg = bg.split()[0]
            fg = _value(code, ba, bb, 'color')
            if fg is not None:
                ink = fg
    if ink is None:
        return None, None, None

    ground, where = own_bg, want
    if ground is None or ground in ('transparent', 'none'):
        # Walk OUT one descendant step at a time, nearest first, exactly
        # as the cascade does. `.undo-toast .toast-undo-btn` asks
        # `.undo-toast`, which paints var(--alv-ink).
        parts = want.split(':')[0].strip().split()
        ground, where = '#ffffff', 'the page'
        while len(parts) > 1:
            parts = parts[:-1]
            anc = ' '.join(parts)
            g = grounds.get(anc)
            if g and g not in ('transparent', 'none'):
                ground, where = g, anc
                break
    return EI.resolve(ink, tok), EI.resolve(ground, tok), where


''' + AMBER_HELPER_ANCHOR

# ---------------------------------------------------------------------------
# the registers
# ---------------------------------------------------------------------------
TREE_WAS = """    'test_panel_heads.py',
]"""
TREE_NOW = """    'test_panel_heads.py',
    # VB-1, 15 Oct 2026 - the verb colours. Demetri asked why a selection
    # was green, why a confirmation bar was brown on brown, and why the
    # Edit button is one colour here and blue everywhere else. Three
    # questions, one answer. Wide from birth.
    'test_verb_colours.py',
]"""

ROUNDS_WAS = """    '.bak_panelheads',
]"""
ROUNDS_NOW = """    '.bak_panelheads',
    # VB-1, 15 Oct 2026 - the chips onto the accent, the toast onto the
    # -line tokens, and the recipe overlay onto the four verb tokens.
    # alv_rowactions gains VERNACULAR so the overlay stops being invisible.
    '.bak_verbs',
]"""

SUITE_WAS = """    'test_panel_heads.py'
)"""
SUITE_NOW = """    'test_panel_heads.py',
    'test_verb_colours.py'
)"""

CLAIMS_ANCHOR = """    @{ File = 'pages\\templates\\pantry_staples.html'; Text = 'var(--alv-good-soft)'; What = 'and 92 pantry chips leave a hex literal no colour census could see' },"""

CLAIMS = """    @{ File = 'pages\\templates\\pantry_staples.html'; Text = 'var(--alv-good-soft)'; What = 'and 92 pantry chips leave a hex literal no colour census could see' },
    # ------------------------------------------------- VB-1, 15 Oct 2026
    # Three questions from the live site and one answer: a colour that
    # names a verb in one module and a different verb in another names
    # nothing. No sentinel below claims a thing was LEFT alone - that
    # belongs in the round's suite, which is where test_sentinels sent
    # the last one I wrote.
    @{ File = 'pages\\templates\\wcim_landing.html'; Text = 'rgba(14, 124, 139, 0.3)'; What = 'the chooser chip stops wearing a Bootstrap green no census could see' },
    @{ File = 'pages\\templates\\wcim_extras.html'; Text = 'var(--alv-accent-soft)'; What = 'and a selection stops being reported as a positive status' },
    @{ File = 'pages\\templates\\map_ingredients_nutrition.html'; Text = 'var(--alv-warn-line)'; What = 'the Undo on the confirmation bar is readable again - 1.60:1 to 8.87:1' },
    @{ File = 'pages\\templates\\unit_conversions_wizard.html'; Text = 'var(--alv-good-line)'; What = 'and the tick beside it clears the glyph floor it was under' },
    @{ File = 'pages\\templates\\recipe_management.html'; Text = 'var(--alv-edit)'; What = 'the recipe Edit button is the same blue as every other module' },
    # NO `Absent` ROW FOR THE DUPLICATE HOVER. The obvious one was
    # var(--alv-accent-ink) marked Absent, and test_bar_order refused it:
    # that token has FIVE other legitimate uses on the page - the letter
    # filter's scrollbar thumb and four tag inks - so the claim was simply
    # false. Second sentinel in two rounds to assert something about what
    # a round REMOVED. The removal is checked in test_verb_colours section
    # 5, where it can name the selector instead of a substring, and that
    # is where it belongs.
    @{ File = 'alv_rowactions.py'; Text = 'VERNACULAR'; What = 'four controls no drift census could see are registered by verb' },"""


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
    raise SystemExit('VB-1 REFUSED: %s' % msg)


def fit(text, lit):
    """A multi-line anchor written LF here, converted to whatever THIS file
    mostly uses. PX-1's hazard, fourth round running: recipe_management is
    CRLF, base.html is not, and an anchor written one way refuses on one
    half of the round or the other."""
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
    # ALREADY APPLIED COMES FIRST, and it is asked of the TREE rather than
    # of a marker this file writes: if no page still carries one of the
    # old blocks, the markup half is done and a second run is a no-op.
    # THE ANCHORS ARE FITTED HERE TOO. Written LF in this file and these
    # five pages are not all LF, so a raw .count() reports zero on a CRLF
    # page and the round cheerfully announces it has already been applied.
    # It did exactly that once before this line was written.
    live = 0
    for page, old, _new, _what in EDITS:
        s = read(alv_tree.path_of(page))
        live += s.count(fit(s, old))
    for page in TOAST_PAGES:
        s = read(alv_tree.path_of(page))
        live += s.count(fit(s, TOAST_ICON_WAS))
    s = read(alv_tree.path_of(RM))
    for old, _new, _what in RM_EDITS:
        live += s.count(fit(s, old))
    if not live:
        print('VB-1  already applied - no control still names the wrong '
              'verb.')
        return 0

    out = {}
    pages = set()

    # ---------------------------------------------------------------- 1
    # the chips
    for page, old, new, what in EDITS:
        p = alv_tree.path_of(page)
        s = out.get(p, read(p))
        out[p] = swap(s, old, new, '%s (%s)' % (page, what))
        pages.add(page)

    # ---------------------------------------------------------------- 2
    # the toast, both declarations on both pages
    for page in TOAST_PAGES:
        p = alv_tree.path_of(page)
        s = out.get(p, read(p))
        s = swap(s, TOAST_ICON_WAS, TOAST_ICON_NOW,
                 '%s (the toast tick)' % page)
        if page in TOAST_BTN_PAGES:
            s = swap(s, TOAST_BTN_WAS, TOAST_BTN_NOW,
                     '%s (the toast Undo)' % page)
        out[p] = s
        pages.add(page)

    # AND THE WIZARD HAS NO UNDO TO FIX. Asserted rather than assumed,
    # because the whole reason this is a gate is that I claimed it did.
    for page in TOAST_PAGES:
        has = 'toast-undo-btn' in read(alv_tree.path_of(page))
        if has != (page in TOAST_BTN_PAGES):
            refuse('%s: toast-undo-btn is %spresent and the round expects '
                   'the opposite' % (page, '' if has else 'not '))

    # ---------------------------------------------------------------- 3
    # the recipe overlay
    p = alv_tree.path_of(RM)
    s = read(p)
    for old, new, what in RM_EDITS:
        s = swap(s, old, new, '%s (%s)' % (RM, what))
    out[p] = s
    pages.add(RM)

    if len(pages) != N_PAGES:
        refuse('expected %d page(s); edited %d' % (N_PAGES, len(pages)))

    # ---------------------------------------------------------------- 4
    # base.html - two comments, no declarations. Asserted, not assumed:
    # a round that claims it changed no value has to prove it, and the
    # proof is that every --alv- line in the file is byte-identical apart
    # from the two comment tails.
    p = alv_tree.path_of(BASE)
    s = read(p)
    before = [ln for ln in s.splitlines() if '--alv-' in ln and ':' in ln]
    for old, new, what in BASE_EDITS:
        s = swap(s, old, new, '%s (%s)' % (BASE, what))
    after = [ln for ln in s.splitlines() if '--alv-' in ln and ':' in ln]
    if len(before) != len(after):
        refuse('%s: the token count moved %d -> %d - this round adds none'
               % (BASE, len(before), len(after)))
    moved = [(a, b) for a, b in zip(before, after) if a != b]
    if len(moved) != len(BASE_EDITS):
        refuse('%s: %d token line(s) changed, expected %d'
               % (BASE, len(moved), len(BASE_EDITS)))
    for a, b in moved:
        if a.split('/*')[0] != b.split('/*')[0]:
            refuse('%s: a VALUE moved, not just a comment - %r'
                   % (BASE, a.strip()[:60]))
    out[p] = s

    # ---------------------------------------------------------------- 5
    # alv_rowactions.py - VERNACULAR
    p = os.path.join(root, RA)
    s = read(p)
    if 'VERNACULAR' in s:
        refuse('%s already holds VERNACULAR' % RA)
    out[p] = swap(s, RA_WAS, RA_NOW, '%s (VERNACULAR)' % RA)

    # ---------------------------------------------------------------- 6
    # test_amber.py - the check that could not fail
    p = os.path.join(root, AMBER)
    s = read(p)
    if '_on_its_real_ground' in s:
        refuse('%s already measures the real ground' % AMBER)
    s = swap(s, AMBER_HELPER_ANCHOR, AMBER_HELPER, '%s (the helper)' % AMBER)
    s = swap(s, AMBER_WAS, AMBER_NOW, '%s (section 4)' % AMBER)
    out[p] = s

    # ---------------------------------------------------------------- 7
    # the registers and the two counters these rounds keep by hand
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_verb_colours.py' in s:
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
                  'VB-1, 15 Oct 2026 - this round own suite. The verb '
                  'colours, after Demetri asked why the Edit button is '
                  'one colour here and blue in every other module.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'VB-1, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 8
    if CHECK:
        print('VB-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('VB-1 applied.')
    print('   %d colour declaration(s) on %d page(s) onto the house verbs'
          % (N_DECLS, N_PAGES))
    print('   %d hover rule(s) dropped - all four controls now behave alike'
          % N_DROPPED)
    print('   the toast Undo 1.60:1 -> 8.87:1, the tick 2.53:1 -> 9.10:1')
    print('   base: 2 comments, 0 declarations - the -line tokens say what')
    print('         they are for on a dark ground, which is why this round')
    print('         nearly minted a fourth one that already existed')
    print('   %d overlay control(s) registered in VERNACULAR, by verb'
          % N_CONTROLS)
    print('   test_amber section 4 measures a ground instead of naming a')
    print('         token - it could not fail for its own reason before')
    print('   %d of %d ancestor-ground pairs fixed; the other %d are named'
          % (N_ANCESTOR_FIXED, N_ANCESTOR, N_ANCESTOR - N_ANCESTOR_FIXED))
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
