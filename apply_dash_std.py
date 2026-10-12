# -*- coding: utf-8 -*-
"""apply_dash_std.py - round DB-5, 12 Oct 2026.

THE PROPERTY DASHBOARD ONTO HOUSE STANDARDS.

Four decisions were banked on 11 Oct from two screenshots. The survey
written before this patcher went back to the file and measured them:
three held, one had a wrong premise, and two things turned up that none
of the four covered. One of those two is larger than all four together.

SURVEY: claude/db5_dashboard_survey_12_oct.md


1. THE CONTROLS, AND THE ONE LINE IN BASE THAT EXPLAINS THEM
-------------------------------------------------------------
The page keeps a 56px vertical column to the right of the teal band
holding a hamburger above a Back arrow, drawn by TEN local rules under
`.dashboard-side-actions` - eight in the desktop block and two more in
the mobile one, which narrow the same column again.

Measured across all 151 templates: 33 pages carry an
`action-more-wrapper`; 32 put it inside a `.page-action-buttons` bar.
This page is the one that does not - and it is the only page in the app
with a local rule naming `.action-more-wrapper` at all.

That rule exists because of ONE line in base, at line 2701, OUTSIDE any
media query:

    .action-more-wrapper { display: none; }

Every other rule for the component - button, menu, items, divider -
sits inside `@media screen and (max-width: 768px)`. BASE'S MORE MENU IS
A PHONE-ONLY COMPONENT. On a desktop the wrapper is hidden and the
`.action-secondary` buttons show; on a phone the secondaries hide and
the menu takes over.

So the dashboard's hamburger is THE ONLY MORE BUTTON IN THE APP THAT IS
VISIBLE ON A DESKTOP, and only because the page overrode base at
specificity (0,2,0).

This is already on the record twice. `test_more_css.py` carries the
page on a SKIP list - "an always-present side hamburger, outside any
.page-action-buttons" - and PROVES the exclusion by stripping the local
rules in a fixture: 44x47 -> 26x14 on a phone, 56x36 -> GONE on a
desktop. `test_last_menus.py` calls it PAINTER, "the one page that
still paints the component".

NEITHER SUITE IS TOUCHED BY THIS ROUND, and that is a measurement, not
an oversight. Both read the page through as_left_by, and the dashboard
already carries six backups later than `.bak_morecss` - the earliest is
`.bak_msgbar` - so both have been reading history, not the live file,
since well before today. Their recorded reasons are measurements of
their own moment and stay true for it. A round that rewrote them
because the live file moved would be the as_left_by lesson from the
wrong side for the fourth time.

The house shape is copied from properties.html, not invented:

    [Choose Property] [Help] [More] ............ [Back]

Help appears twice on purpose - a desktop secondary AND the single item
in the phone More menu. That is what all 32 reference pages do, and it
is why the hamburger disappearing on a desktop is the answer rather
than a loss. All nine local rules go, and the page ends with NO
action-bar CSS of its own.


2. `.dash-card` -> `.alv-card` - THE PREMISE WAS WRONG
------------------------------------------------------
`.alv-card` is a container with a head and a 20px bottom margin. A tile
is a centred icon over a label at a 130px minimum height. Converted
literally, every tile gains 20px below it on top of the grid's 16px
gap, and the centring, the height and the 32px icon all have to be
written back locally. Nothing is gained.

And the drift is smaller than it looked. Measured side by side, the
background and the border are ALREADY byte-identical house tokens - the
B-1/B-2 rounds did that. The only real drift is `border-radius: 10px`.

Surveyed further: BASE HAS NO TILE COMPONENT AT ALL. No `.alv-tile`, no
card grid. Of 151 templates six draw an icon-over-label clickable grid
and all six use private names. So `.dash-card` is not a drift from a
house component - IT IS A COMPONENT THE HOUSE HAS NEVER NAMED, and this
round does not pretend otherwise. The tile keeps its layout and takes
the radius token.


3. THE PAGE DIMS FOUR TIMES, AND NO GATE CAN SEE IT
---------------------------------------------------
Four `opacity` declarations. Neither test_pair_contrast.py nor
test_contrast.py contains the word `opacity` - every contrast gate in
the system reads declared colour pairs - so all four have passed every
sweep since the page was written.

  a. `.dashboard-grids { opacity: 0.45 }` is the state you LAND in.
     Tile label declares 12.95:1, renders at 2.54:1.
     Tile icon  declares  4.91:1, renders at 1.91:1.
     AA wants 4.5 for body text and 3.0 for large. Every label on the
     page you arrive at is below both.

  b. A permission-denied tile is dimmed TWICE - `#adb5bd` AND
     `opacity: 0.5`. Composited: #d6dade on #f8f9fa = 1.33:1. The
     house's own switched-off recipe, with no opacity, is 2.53:1. This
     is E-10's lesson from the other side: there, a switched-off button
     was the only one in the app that was not grey; here a tile a user
     has no permission for is UNREADABLE, so they cannot tell what they
     are being denied.

  c. `CURRENT PROPERTY` at opacity .85 on the accent: 4.01:1, at 13px.
  d. `Click to choose` at opacity .80 on the accent: 3.75:1, at 13px.

WHAT THIS ROUND DOES ABOUT EACH:

  a -> 0.75, which is not a taste. Measured at every step: the accent
       icon clears 3.0 at .75 (3.14:1) and fails at .70 (2.90:1). The
       label is 5.87:1 there. .75 is the LOWEST dim at which both pass,
       so the signal is kept and the floor is met.
  b -> the opacity goes and `#adb5bd` becomes `--alv-ink-soft`:
       4.97:1 on `--alv-line-soft`, up from 1.33:1. `--alv-ink-faint`
       was measured too and is only 2.70:1 there, so this is a choice
       between two house tokens on the numbers, not an invention. The
       tile still reads as off - the wash ground, the `--alv-line`
       border, `cursor: not-allowed` and `pointer-events: none` all
       stay.
  c -> becomes the `.alv-card-head` title, no opacity.
  d -> DELETED. "Click to choose" is an instruction standing in for a
       button, and the button now exists. Both sub-4.5 items are solved
       by the structural change rather than by tuning an opacity.


4. THE PAGE CANNOT BE USED FROM A KEYBOARD
------------------------------------------
Bigger than the four styling decisions together.

    <div class="property-selector-card" id="propertySelectorCard">
    <div class="dash-card" data-box-type="property-report">
    <div class="property-picker-item" data-property-id="...">

All three are plain `<div>`s with a `click` listener and nothing else -
no role, no tabindex, no keydown handler. Verified against the page's
own script: three addEventListener('click') bindings and no key
handling anywhere.

TAB THROUGH THE PROPERTY DASHBOARD AND YOU REACH THE HAMBURGER AND THE
BACK LINK. THAT IS ALL. You cannot choose a property, and you cannot
open any of the 12 tiles.

The 12 tiles cannot simply become `<a href>`: they navigate to
/property_detail/<id>/<boxType>/ and THE PROPERTY ID IS NOT KNOWN AT
RENDER TIME - it is chosen client-side, in the modal. So:

  - the selector becomes a real `<button class="btn action-primary">`
    in the bar. Focusable and Enter-activated by definition.
  - the 12 tiles become real `<a>` elements whose href the JS sets when
    a property is chosen. Keyboard, focus ring, middle-click and
    open-in-new-tab all arrive for free.
  - the picker rows become `<button type="button">`. They are actions
    in a modal - they set state and close it - not navigation.
  - the 12 permission-denied twins STAY `<div>`s. They are not links.

AND IT COLLAPSES 3a. An `<a>` with no `href` is not focusable and not
clickable, so THE ABSENCE OF AN HREF IS THE LOCK. The page no longer
needs `pointer-events: none` on the grid to enforce the unarmed state,
which is why the dim can come up from .45 to .75: it went from being
the lock to being the signal.

WHAT IS DELIBERATELY LOST: `.dash-card.clicked` and the 200ms
setTimeout before navigation. A real link navigates on click and the
browser's own feedback is the feedback; keeping the animation would
mean preventDefault and a timer, which puts the JS dependence back and
breaks middle-click. One rule and nine lines of script go with it.


WHAT THIS ROUND DOES NOT DO
---------------------------
It does not touch base - everything it needs is already there. It does
not name a house tile component; that is a real question and it is not
answered by one page. It does not touch the picker modal's header, the
Help modal, the three section groupings, the twelve destinations, or
any permission test. And it does not claim the four dims were drift:
three were decisions taken when nothing could measure them, and the
fourth was an instruction where a button belonged.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alv_tree                                            # noqa: E402

SUFFIX = '.bak_dashstd'
SUITE = 'test_dash_std.py'
PAGE = 'pages/templates/property_management_dashboard.html'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CHECK = False

REFERENCE = 'properties.html'

# Measured, both roots, 12 Oct. The patcher refuses rather than guessing.
MORE_PAGES = 33            # templates carrying an action-more-wrapper
MORE_IN_BAR = 32           # of those, inside a .page-action-buttons
TILES = 12                 # live tiles
TWINS = 12                 # permission-denied twins
LOCAL_RULES_WAS = 52       # rules in the page's own <style>
SIDE_RULES = 10            # .dashboard-side-actions* rules, all deleted
# TEN, NOT NINE. The survey said nine, counting the desktop block
# and forgetting that the mobile block narrows the same column
# again in two more rules. The gate above refused on its own
# round's figure, which is what an exact-count gate is for.

DIM_WAS, DIM_NOW = '0.45', '0.75'

CONVERTED_WAS, CONVERTED_NOW = 66, 67

# A PINNED COUNT MOVES. test_code_only pins how many files alias the
# house stripper, and DB-5 adds two - a patcher and a suite. The round
# that moves a census owns the number that counts it.
CO = 'test_code_only.py'
ALIAS_WAS, ALIAS_NOW = 45, 47

# AND test_bar_height's census, for the same reason. Moving the page's
# controls into the house bar moves them from its LOOSE set into its BAR
# set, and the two heights the side column invented stop existing:
#
#   bar controls          265 -> 268
#   loose controls         82 -> 80
#   distinct loose heights  12 -> 10
#
# That last one is the round in a number. The page drew a 56px column
# with a 44px phone variant, and both were heights nothing else in the
# app used. A pinned COUNT moves; a pinned DECISION does not; and this
# census was never either - it is a measurement, and it has changed.
# AND E-10's SUITE, WHICH READS THOSE TWO CENSUSES - LIVE.
#
# test_drift_root checks that E-10 moved them, and does it by reading
# test_bar_height.py and test_pair_contrast.py OFF DISK TODAY:
#
#     bh = read(os.path.join(ROOT, 'test_bar_height.py'))
#
# So the moment any later round re-pins either census, E-10's suite
# reports that E-10 did something it did not do. DB-5 is that round, and
# it failed exactly there: "the twelve distinct loose heights did not
# move [10]".
#
# THE FIX IS NOT TO RE-PIN E-10's THREE NUMBERS. That is the treadmill,
# and this programme already has the mechanism that ends it: a suite
# asking about its OWN round must read the file as its own round left
# it. as_left_by walks ROUNDS forward from .bak_driftroot to the first
# later backup - which, after today, is .bak_dashstd - and hands back
# exactly the file E-10 shipped. All three checks then pass unchanged,
# and keep passing for every round after this one.
#
# alv_rounds is already imported in that suite. Two lines move.
# (Lesson 40, from the side that gives rather than takes.)
DR = 'test_drift_root.py'

# HL-1's two censuses. DB-5 gives the dashboard a Help secondary and a
# Back label it did not have, so both counts rise by exactly one. These
# ARE counts of the live tree by design - HL-1's claim is "every Help
# control in the app writes bare text", which has to stay true of the
# app and not of a snapshot - so here re-pinning is the right answer and
# as_left_by would be the wrong one.
HLP = 'test_help_label.py'
LABELS_WAS, LABELS_NOW = 129, 130
HELPS_WAS, HELPS_NOW = 40, 41

# And the pair census, which loses the four rules that set both a
# background and a colour on the teal slab and the side menu.
PC = 'test_pair_contrast.py'
PAIRS_WAS, PAIRS_NOW = 716, 712

BH = 'test_bar_height.py'
BAR_WAS, BAR_NOW = 265, 268
LOOSE_WAS, LOOSE_NOW = 82, 80
LOOSEH_WAS, LOOSEH_NOW = 12, 10


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
    raise SystemExit('DB-5 REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:70], n))


def exactly(text, lit, n, where):
    got = text.count(lit)
    if got != n:
        refuse('%s: %r appears %d time(s), expected exactly %d'
               % (where, lit[:70], got, n))


def crlf(s):
    """Every line in this template ends CRLF - 751 of 751, measured. An
    anchor written with bare LF matches nothing, and a replacement
    written with bare LF leaves a file with two line endings in it."""
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def css_rules(text):
    """The selectors in the page's own <style> blocks, in order."""
    out = []
    for m in re.finditer(r'<style[^>]*>([\s\S]*?)</style>', text):
        for s in re.finditer(r'(?m)^\s*([.#][^\n{}]*?)\s*\{', m.group(1)):
            out.append(s.group(1).strip())
    return out


# ======================================================================
# 1. THE ACTION BAR. Copied from properties.html, not invented.
# ======================================================================
TOP_WAS = """  <!-- Top Row: Property Selector (left) + Side Actions (right column with hamburger + back stacked) -->
  <div class="dashboard-top-row">
    <!-- Property Selector Card -->
    <div class="property-selector-card" id="propertySelectorCard">
      <div class="selector-inner">
        <div class="selector-label">
          <i class="fas fa-building"></i> Current Property
        </div>
        <div class="selector-value" id="propertyDisplayText">Click to select a property</div>
        <div class="selector-hint">
          <i class="fas fa-mouse-pointer"></i> Click to choose
        </div>
      </div>
    </div>

    <!-- Side actions: hamburger (More menu — currently just Help) on top, Back below -->
    <div class="dashboard-side-actions">
      <div class="action-more-wrapper" data-menu>
        <button type="button" class="btn action-more-btn" id="actionMoreBtn" data-menu-toggle
                aria-label="More actions" aria-expanded="false" aria-haspopup="true">
          <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
          <button type="button" class="action-more-item" role="menuitem"
                  data-toggle="modal" data-target="#dashboardHelpModal">
            <i class="fas fa-question-circle"></i> Help
          </button>
        </div>
      </div>
      <a href="{% url 'home' %}" class="btn action-back action-back-stacked"
         role="button" aria-label="Back to home">
        <i class="fas fa-arrow-left"></i>
      </a>
    </div>
  </div>
"""

TOP_NEW = """{# DB-5, 12 Oct 2026 - the house action bar, the shape properties.html #}
  {# has. WAS a 56px side column holding a hamburger above a Back arrow, #}
  {# drawn by ten local rules, outside any .page-action-buttons. Of 33 #}
  {# pages carrying an action-more-wrapper, 32 put it in the bar; this #}
  {# was the one that did not, and the only page in the app with a local #}
  {# rule naming that class - because base hides the wrapper OUTSIDE any #}
  {# media query and styles the rest of the component only below 768px. #}
  {# Base's More menu is a PHONE component. Help is a desktop secondary #}
  {# and a phone menu item, which is why both appear below. #}
  <div class="page-action-buttons">
    <button type="button" class="btn action-primary" id="choosePropertyBtn">
      <i class="fas fa-building"></i> Choose Property
    </button>

    <!-- Desktop-visible secondary buttons (hidden on mobile, accessed via "More" menu) -->
    <button type="button" class="btn action-secondary"
            data-toggle="modal" data-target="#dashboardHelpModal">
      <i class="fas fa-question-circle"></i> Help
    </button>

    <!-- Mobile-only "More" dropdown -->
    <div class="action-more-wrapper" data-menu>
      <button type="button" class="btn action-more-btn" id="actionMoreBtn" data-menu-toggle
              aria-label="More actions" aria-expanded="false" aria-haspopup="true">
        <i class="fas fa-ellipsis-v"></i>
      </button>
      <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
        <button type="button" class="action-more-item" role="menuitem"
                data-toggle="modal" data-target="#dashboardHelpModal">
          <i class="fas fa-question-circle"></i> Help
        </button>
      </div>
    </div>

    <a href="{% url 'home' %}" class="btn action-back" aria-label="Back to home">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>

{# The chosen property, on base's own card. WAS a teal gradient slab #}
  {# whose own 13px label read 4.01:1 at opacity .85 and whose hint read #}
  {# 3.75:1 at .80 - and the hint said "Click to choose", an instruction #}
  {# standing in for the button that now sits above. The teal has not #}
  {# gone from the page; it stays in the twelve tile icons and the three #}
  {# section underlines, where it carries information. DB-8's rule. #}
  <div class="alv-card alv-chosen-property">
    <div class="alv-card-head">
      <i class="fas fa-building"></i>
      <span class="alv-card-title">Current Property</span>
    </div>
    <div class="alv-card-body">
      <div class="chosen-property-name" id="propertyDisplayText">No property chosen yet</div>
    </div>
  </div>
"""

# ======================================================================
# 2. THE TILES. A real link, with no href until a property is chosen.
# ======================================================================
TILE_WAS = '          <div class="dash-card" data-box-type="'
TILE_NEW = '          <a class="dash-card" data-box-type="'

# The close tag of a live tile. The twin below keeps its own `</div>`,
# so this is anchored on the label line and the `{% else %}` that
# follows it rather than on `</div>` alone - which appears 40 times.
#
# @LABEL@ rather than %s: the anchor contains `{% else %}`, and a
# percent-formatted string containing a Django tag is a TypeError
# waiting for the one caller who forgets to double the sign.
TILE_END_WAS = ('            <div class="dash-card-label">@LABEL@</div>\r\n'
                '          </div>\r\n'
                '        {% else %}')
TILE_END_NEW = ('            <div class="dash-card-label">@LABEL@</div>\r\n'
                '          </a>\r\n'
                '        {% else %}')


def tile_end(tpl, label):
    return tpl.replace('@LABEL@', label)

LABELS = ['Property Report', 'Title Deed', 'Valuation', 'Issues',
          'Tenant Report', 'Lease', 'Invoices', 'Lease Renewals',
          'Revenues', 'Actual Expenses', 'Budgeted Expenses',
          'Profit &amp; Loss']

# ======================================================================
# 3. THE PICKER ROWS. A button, because they act and close a modal.
# ======================================================================
PICK_WAS = """              <div class="property-picker-item"
                   data-property-id="{{ property.prop_id }}"
                   data-property-name="{{ property.prop_name }}">
                <i class="fas fa-home"></i>
                <span>{{ property.prop_name }}</span>
                <i class="fas fa-chevron-right picker-chevron"></i>
              </div>
"""

PICK_NEW = """{# DB-5 - a button, not a div. These rows had a click #}
              {# listener and nothing else: no role, no tabindex, no key #}
              {# handler, so the property could not be chosen from a #}
              {# keyboard at all. They act and close the modal rather #}
              {# than navigate, which is what a button is. #}
              <button type="button" class="property-picker-item"
                      data-property-id="{{ property.prop_id }}"
                      data-property-name="{{ property.prop_name }}">
                <i class="fas fa-home"></i>
                <span>{{ property.prop_name }}</span>
                <i class="fas fa-chevron-right picker-chevron"></i>
              </button>
"""


# ======================================================================
# 4. THE CSS. Nine rules for the side column, four for the teal slab and
#    two for a private copy of base's section heading all go; the rest
#    moves onto tokens.
#
#    BLOCK A is replaced BY ITS BOUNDS, not by a 150-line literal. Each
#    bound is asserted to appear exactly once, which is the same gate a
#    literal would give and does not put 150 lines of someone else's
#    formatting inside this file where a single space would break it.
# ======================================================================
A_FROM = ('/* ==================== TOP ROW: Property Selector + Side '
          'Actions ==================== */')
A_TO = '/* ==================== DASHBOARD SECTIONS ==================== */'

A_NEW = """/* ==================== THE CHOSEN PROPERTY ==================== */
/* DB-5, 12 Oct 2026 - what used to be here:
     .dashboard-top-row               the two-column shell
     .property-selector-card  x3      a teal gradient slab, clickable
     .selector-inner / -label / -value / -hint
     .dashboard-side-actions  x8      a 56px column: hamburger + Back
   Twenty-one declarations of a More menu that base already owns, and a
   100px teal slab whose 13px label read 4.01:1 and whose hint read
   3.75:1 because both were dimmed with opacity - which no contrast gate
   in this system can see. The bar above is base's. The card is base's.
   What is left here is the one thing base has no name for: how big the
   property's name should be. */
.chosen-property-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--alv-ink);
  word-break: break-word;
}

"""

B_WAS = """.section-title {
  color: var(--alv-ink);
  font-weight: 600;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--alv-accent);
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title i {
  color: var(--alv-accent);
}

"""

B_NEW = """/* DB-5 - .section-title and .section-title i are GONE. They were a
   private copy of base's .form-section-title, which declares the same
   --alv-ink, the same weight 600, the same 2px solid var(--alv-accent)
   bottom border and the same accent icon. Measured identical, so the
   markup joins the component instead of restating it. */

"""

# ---- the grid's dim ---------------------------------------------------
DIM_WAS_RULE = """.dashboard-grids {
  opacity: 0.45;
  pointer-events: none;
  transition: opacity 0.3s ease;
}"""

DIM_NEW_RULE = """.dashboard-grids {
  /* DB-5 - WAS 0.45 with pointer-events: none.
     0.45 put the tile label at 2.54:1 and the accent icon at 1.91:1,
     and that is the state you LAND in. Measured at every step: the icon
     clears 3.0 at .75 (3.14:1) and fails at .70 (2.90:1); the label is
     5.87:1 at .75. So .75 is the LOWEST dim that keeps the signal and
     meets the floor - it is a measurement, not a taste.
     pointer-events is gone because it is no longer what locks the page.
     The tiles are anchors now and carry no href until a property is
     chosen, and an <a> with no href is neither focusable nor clickable.
     THE ABSENCE OF AN HREF IS THE LOCK; this is only the signal. */
  opacity: 0.75;
  transition: opacity 0.3s ease;
}"""

# ---- the tile --------------------------------------------------------
CARD_WAS = """.dash-card {
  background: var(--alv-paper);
  border: 1px solid var(--alv-line);
  border-radius: 10px;"""

CARD_NEW = """.dash-card {
  background: var(--alv-paper);
  border: 1px solid var(--alv-line);
  /* DB-5 - WAS a 10px literal. Base has no tile component at all, so
     this is not a drift from one; of 151 templates six draw an
     icon-over-label grid and all six use private names. What the tile
     IS is a card, so it takes the radius every house card takes.
     D-12 converted only the 6px literals and left every other value
     alone, which is why this one survived that round. */
  border-radius: var(--alv-radius-sm);
  text-decoration: none;"""

CARD_CURSOR_WAS = """  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;"""

CARD_CURSOR_NEW = """  text-align: center;
  transition: all 0.25s ease;"""

HOVER_WAS = """.dash-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(14, 124, 139, 0.15);
  border-color: var(--alv-accent);
}

.dash-card:hover .dash-card-icon {
  color: var(--alv-accent-ink);
  transform: scale(1.1);
}"""

HOVER_NEW = """/* DB-5 - scoped to [href]. An unarmed tile is an <a> with no href: it
   must not offer a pointer, a lift or a focus ring for something that
   cannot be opened yet. */
a.dash-card[href] {
  cursor: pointer;
}

a.dash-card[href]:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(14, 124, 139, 0.15);
  border-color: var(--alv-accent);
}

a.dash-card[href]:hover .dash-card-icon {
  color: var(--alv-accent-ink);
  transform: scale(1.1);
}

/* The ring base gives every control in an action bar. These tiles were
   unreachable by keyboard until this round, so they had never needed
   one. Same declaration as base's .page-action-buttons .btn. */
a.dash-card[href]:focus-visible {
  outline: 2px solid var(--alv-accent);
  outline-offset: 2px;
}"""

CLICKED_WAS = """/* Active/clicked state */
.dash-card.clicked {
  transform: scale(0.97);
  box-shadow: 0 2px 6px rgba(14, 124, 139, 0.3);
  background: var(--alv-accent-soft);
}

"""

CLICKED_NEW = """/* DB-5 - .dash-card.clicked is GONE, with the nine lines of script that
   drove it. A real link navigates on click and the browser's own
   feedback is the feedback; keeping a 300ms scale and a 200ms timer
   would mean preventDefault, which puts back the JavaScript dependence
   this round removed and breaks middle-click and open-in-new-tab. */

"""

DIS_WAS = """.dash-card.dash-card-disabled {
  background: var(--alv-line-soft);
  border-color: var(--alv-line);
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}"""

DIS_NEW = """.dash-card.dash-card-disabled {
  /* DB-5 - the opacity is GONE. This tile was dimmed TWICE: #adb5bd
     text AND opacity 0.5, which composited to #d6dade on #f8f9fa =
     1.33:1. A user without the permission could not read what they were
     being denied. The house's own switched-off recipe carries no opacity
     at all, and the ground, the border and the two locks below are what
     say "off". E-10's lesson from the other side. */
  background: var(--alv-line-soft);
  border-color: var(--alv-line);
  cursor: not-allowed;
  pointer-events: none;
}"""

DIS_ICON_WAS = """.dash-card.dash-card-disabled .dash-card-icon {
  color: #adb5bd;
}

.dash-card.dash-card-disabled .dash-card-label {
  color: #adb5bd;
}"""

DIS_ICON_NEW = """/* DB-5 - WAS #adb5bd, which is 35 RGB units off --alv-ink-faint and so
   sat above B-2b's 25-unit bound: a visible move, which is exactly why
   the colour rounds left it alone rather than sweeping it.
   Chosen on the numbers between the two candidate tokens:
     --alv-ink-faint on --alv-line-soft   2.70:1
     --alv-ink-soft  on --alv-line-soft   4.97:1
   up from 1.33:1 as the tile actually rendered. */
.dash-card.dash-card-disabled .dash-card-icon {
  color: var(--alv-ink-soft);
}

.dash-card.dash-card-disabled .dash-card-label {
  color: var(--alv-ink-soft);
}"""

# ---- the picker rows -------------------------------------------------
PICKCSS_WAS = """.property-picker-item {
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--alv-line-soft);
  transition: all 0.2s ease;
}"""

PICKCSS_NEW = """.property-picker-item {
  /* DB-5 - a <button> now, so the four declarations a button brings of
     its own have to be answered: the UA border, the UA background, the
     centred text and the UA font. Nothing else about the row moves. */
  width: 100%;
  background: none;
  border: 0;
  border-bottom: 1px solid var(--alv-line-soft);
  font: inherit;
  text-align: left;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.property-picker-item:focus-visible {
  outline: 2px solid var(--alv-accent);
  outline-offset: -2px;
}"""

CHEV_WAS = """.picker-chevron {
  color: #adb5bd;"""

CHEV_NEW = """.picker-chevron {
  /* DB-5 - 2.07:1 on paper as a literal, 3.00:1 on the token. */
  color: var(--alv-ink-faint);"""

# ---- the mobile block ------------------------------------------------
M_FROM = """@media screen and (max-width: 768px) {

  .dashboard-top-row {
    gap: 8px;
    margin-bottom: 20px;
  }

  .property-selector-card {
    padding: 16px 18px;
  }

  .selector-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .selector-label {
    font-size: 11px;
    letter-spacing: 0.6px;
  }

  .selector-value {
    font-size: 16px;
    min-width: 0;
  }

  .selector-hint {
    font-size: 11px;
  }

  /* Side actions — narrower column on mobile */
  .dashboard-side-actions {
    width: 44px;
    gap: 6px;
  }

  .dashboard-side-actions .action-more-btn,
  .dashboard-side-actions .action-back-stacked {
    font-size: 16px;
  }

  .dashboard-grid {"""

M_NEW = """@media screen and (max-width: 768px) {

  /* DB-5 - eight rules went from here with the slab and the side
     column. Base already shrinks the bar to one row on a phone, hides
     the secondaries, opens the More menu and gives Back a 44px square,
     so there is nothing left for this page to say about any of it. */
  .chosen-property-name {
    font-size: 16px;
  }

  .dashboard-grid {"""

# ======================================================================
# 5. THE SCRIPT.
# ======================================================================
JS_WAS = """  var selectorCard = document.getElementById('propertySelectorCard');
  var propertyDisplayText = document.getElementById('propertyDisplayText');
  var dashboardGrids = document.getElementById('dashboardGrids');
  var pickerItems = document.querySelectorAll('.property-picker-item');
  // Only bind click handlers to ACTIVE cards - disabled cards have no data-box-type
  var dashCards = document.querySelectorAll('.dash-card[data-box-type]');

  // Open picker modal when selector card is clicked
  selectorCard.addEventListener('click', function() {
    $('#propertyPickerModal').modal('show');
  });
"""

JS_NEW = """  var chooseBtn = document.getElementById('choosePropertyBtn');
  var propertyDisplayText = document.getElementById('propertyDisplayText');
  var dashboardGrids = document.getElementById('dashboardGrids');
  var pickerItems = document.querySelectorAll('.property-picker-item');
  // The twelve live tiles. The permission-denied twins stay <div>s and
  // carry no data-box-type, so they are not in this list and never gain
  // an href.
  var dashCards = document.querySelectorAll('a.dash-card[data-box-type]');

  // DB-5 - a real button in the action bar. WAS a click listener on a
  // <div> with no role, no tabindex and no key handler, which is why
  // the property could not be chosen from a keyboard at all.
  chooseBtn.addEventListener('click', function() {
    $('#propertyPickerModal').modal('show');
  });
"""

JS_CARDS_WAS = """  // Handle card clicks (navigation)
  dashCards.forEach(function(card) {
    card.addEventListener('click', function() {
      if (!selectedProperty) {
        return; // Cards are pointer-events:none when no property, but safety check
      }

      var boxType = card.getAttribute('data-box-type');

      // Visual feedback
      card.classList.add('clicked');
      setTimeout(function() { card.classList.remove('clicked'); }, 300);

      // Navigate
      setTimeout(function() {
        if (boxType === 'profit-loss') {
          window.location.href = '/property/' + selectedProperty + '/profit-loss/';
        } else {
          window.location.href = '/property_detail/' + selectedProperty + '/' + boxType + '/';
        }
      }, 200);
    });
  });
"""

JS_CARDS_NEW = """  // DB-5 - THE TILES HAVE NO CLICK HANDLER. They are links, and the
  // browser opens a link. What the script does instead is fill in the
  // href once a property is chosen - the destination cannot be in the
  // markup because the property id is not known at render time.
  //
  // The two URL shapes are the ones this page already computed, moved
  // from the click handler to here unchanged.
  function hrefFor(boxType, propId) {
    if (boxType === 'profit-loss') {
      return '/property/' + propId + '/profit-loss/';
    }
    return '/property_detail/' + propId + '/' + boxType + '/';
  }
"""

JS_SEL_WAS = """  // Selection handler
  function selectProperty(propId, propName) {
    selectedProperty = propId;
    selectedPropertyName = propName;
    propertyDisplayText.textContent = propName;
    selectorCard.classList.add('property-selected');
    dashboardGrids.classList.add('armed');
  }
"""

JS_SEL_NEW = """  // Selection handler
  function selectProperty(propId, propName) {
    selectedProperty = propId;
    selectedPropertyName = propName;
    propertyDisplayText.textContent = propName;
    // DB-5 - this is the moment the twelve tiles become openable, and
    // giving them an href is the whole of it: focusable, Enter-
    // activated, middle-clickable, and no longer held shut by a
    // pointer-events rule that a keyboard never consulted anyway.
    dashCards.forEach(function(card) {
      card.setAttribute('href',
        hrefFor(card.getAttribute('data-box-type'), propId));
    });
    dashboardGrids.classList.add('armed');
  }
"""


# ======================================================================
# 6. MARKUP ODDS AND ENDS
# ======================================================================
FLUID_WAS = '<div class="container-fluid">'
FLUID_NEW = ('{# DB-5 - WAS container-fluid. 8 of 151 templates use it, 96 use #}\n'
             '{# plain container. On a 1920 screen a tile goes from ~457px to #}\n'
             '{# ~265px wide; the column count does not change at any width, #}\n'
             '{# so no row reflows - measured, not assumed. #}\n'
             '<div class="container">')

SEC_WAS = '<h5 class="section-title">'
SEC_NEW = '<h5 class="form-section-title">'
SEC_N = 3

GT_SENTINEL_AFTER = (
    "    # -------------------------------------------- HL-1, 12 Oct 2026")



def alvjoin(root, name):
    return os.path.join(root, 'pages', 'templates', name)


# NO PRIVATE STRIPPER HERE. The first draft of this round defined
# `code_only` in this file and again in its suite - and test_code_only.py
# refused both, because alv_tree ALREADY DEFINES IT and that suite exists
# to stop exactly this. Logged as E15 the wrong way round: the hoist has
# already happened, and what was missing was me looking.
#
# alv_tree.code_only_js is also BETTER than the copy I wrote. Mine blanked
# every /* ... */ in the file; the house one does that only inside <style>
# and <script>, because `/*` IS NOT A COMMENT OPENER IN MARKUP -
# accept="image/*" puts one inside an attribute and blanking from there
# costs 94 lines of the Add Passport form. That lesson is already paid
# for and written down. CO-1, 3 Oct.
# THE HOUSE STRIPPER, ALIASED - NOT A SIXTH PRIVATE COPY.
#
# The first draft of this round DEFINED code_only here and again in its
# suite, and test_code_only.py refused both: "no other file in the tree
# defines code_only". That suite exists precisely to stop this. 45 files
# alias it - 22 patchers and 23 suites - and 47 defined it before CO-1
# hoisted it on 3 Oct.
#
# Wrapping it in a def of my own was the SECOND wrong answer: a function
# that calls the house one is still a definition, and the suite counts
# definitions. The house pattern is an assignment.
#
# And the copy I wrote was worse than the one already on the shelf. Mine
# blanked every /* ... */ in the file; the house one does that only
# inside <style> and <script>, because `/*` IS NOT A COMMENT OPENER IN
# MARKUP - accept="image/*" puts one inside an attribute value, and
# blanking from there costs 94 lines of the Add Passport form. That is
# measured, written down, and three weeks old.
#
# code_only, NOT code_only_js. The _js variant also strips // line
# comments inside a <script>, and test_code_only pins it to "exactly the
# three suites that need it" - taking it would have made that four for
# no reason. Measured both against all seventeen counts below: identical
# answers, because nothing this round counts hides behind a // comment.
# Take what you need, not what is nearest.
#
# A GATE READS CODE, NOT THE RECORD OF CODE. The sixth time round, the
# answer was already in alv_tree and the only new thing was my not
# looking.
code_only = alv_tree.code_only


def outside_media(base, needle):
    """True when `needle` sits in base at a point no @media block is
    open. Counts braces from the start, which is crude and exact enough
    for a declaration-free check: base writes @media at one level."""
    i = base.find(needle)
    if i < 0:
        return False
    head = base[:i]
    for m in re.finditer(r'@media[^{]*\{', head):
        depth = 1
        j = m.end()
        while j < i and depth:
            if base[j] == '{':
                depth += 1
            elif base[j] == '}':
                depth -= 1
            j += 1
        if depth:
            return False
    return True


def inside_media(base, needle):
    i = base.find(needle)
    return i >= 0 and not outside_media(base, needle)



def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page_p = os.path.join(root, *PAGE.split('/'))

    # ---------------------------------------------------------------- 0
    # A PATCHER VERIFIES, THEN WRITES - and the already-applied check
    # comes FIRST, before any anchor is looked for, or a second run
    # reports a missing anchor as a broken file.
    if not os.path.isfile(page_p):
        refuse('%s is not on disk' % PAGE)
    page = read(page_p)
    if 'class="page-action-buttons"' in page:
        print('DB-5  already applied - the page is on the house action bar.')
        return 0

    # ---------------------------------------------------------------- 1
    # WHAT THE ROUND MEASURED. If this is not the file that was
    # surveyed, nothing below should run.
    rules = css_rules(page)
    if len(rules) != LOCAL_RULES_WAS:
        refuse('%s has %d local rules, the survey counted %d'
               % (PAGE, len(rules), LOCAL_RULES_WAS))
    side = [r for r in rules if 'dashboard-side-actions' in r]
    if len(side) != SIDE_RULES:
        refuse('expected %d .dashboard-side-actions rules, found %d: %s'
               % (SIDE_RULES, len(side), side))
    exactly(page, TILE_WAS, TILES, PAGE)
    exactly(page, 'dash-card dash-card-disabled', TWINS, PAGE)
    exactly(page, crlf(A_FROM), 1, PAGE)
    exactly(page, crlf(A_TO), 1, PAGE)
    if 'opacity: %s;' % DIM_WAS not in page:
        refuse('the grid dim is not %s - the survey measured it there'
               % DIM_WAS)

    # CONTROL: base really does hide the More wrapper OUTSIDE a media
    # query and style the rest of the component only inside one. That
    # one line is the whole reason the side column existed and the whole
    # reason Help arrives as a desktop secondary. If base ever moves it,
    # this round's reasoning is stale and it must stop rather than
    # quietly do something else.
    base = read(alvjoin(root, 'base.html'))
    if not outside_media(base, '.action-more-wrapper { display: none; }'):
        refuse('base no longer hides .action-more-wrapper outside a media '
               'query - DB-5 reasons from that line, so it must not run '
               'against a base where it has moved')
    if not inside_media(base, '.page-action-buttons .action-more-btn {'):
        refuse('base no longer styles .action-more-btn inside a media query '
               '- the More menu may no longer be phone-only, and Help as a '
               'desktop secondary was chosen on the strength of that')

    # ---------------------------------------------------------------- 2
    # THE PAGE.
    n = page
    once(n, FLUID_WAS, PAGE)
    n = n.replace(FLUID_WAS, crlf(FLUID_NEW), 1)

    exactly(n, SEC_WAS, SEC_N, PAGE)
    n = n.replace(SEC_WAS, SEC_NEW)

    n = n.replace(crlf(TOP_WAS), crlf(TOP_NEW), 1)

    n = n.replace(TILE_WAS, TILE_NEW)
    for lab in LABELS:
        was = tile_end(TILE_END_WAS, lab)
        once(n, was, PAGE)
        n = n.replace(was, tile_end(TILE_END_NEW, lab), 1)

    n = n.replace(crlf(PICK_WAS), crlf(PICK_NEW), 1)

    # ---- the CSS, block A by its bounds ------------------------------
    a = n.index(crlf(A_FROM))
    b = n.index(crlf(A_TO))
    if b <= a:
        refuse('the CSS bounds are in the wrong order')
    n = n[:a] + crlf(A_NEW) + n[b:]

    for was, new in ((B_WAS, B_NEW),
                     (DIM_WAS_RULE, DIM_NEW_RULE),
                     (CARD_WAS, CARD_NEW),
                     (CARD_CURSOR_WAS, CARD_CURSOR_NEW),
                     (HOVER_WAS, HOVER_NEW),
                     (CLICKED_WAS, CLICKED_NEW),
                     (DIS_WAS, DIS_NEW),
                     (DIS_ICON_WAS, DIS_ICON_NEW),
                     (PICKCSS_WAS, PICKCSS_NEW),
                     (CHEV_WAS, CHEV_NEW),
                     (M_FROM, M_NEW),
                     (JS_WAS, JS_NEW),
                     (JS_CARDS_WAS, JS_CARDS_NEW),
                     (JS_SEL_WAS, JS_SEL_NEW)):
        once(n, crlf(was), PAGE)
        n = n.replace(crlf(was), crlf(new), 1)

    npage = n

    # ---------------------------------------------------------------- 3
    # THE GATES, EVERY ONE OF THEM AGAINST THE COMMENT-STRIPPED TEXT.
    # See code_only: this round's comments name the very classes it
    # deletes, so a gate on the raw file would refuse on its own
    # explanation. Fifth occurrence of that mistake, caught while
    # writing the note about the first four.
    code = code_only(npage)
    for lit, want, what in (
            ('.dashboard-side-actions', 0, 'the side column'),
            ('property-selector-card', 0, 'the teal slab, CSS and markup'),
            ('selector-label', 0, 'the slab label'),
            ('selector-hint', 0, 'the instruction that stood in for a '
             'button'),
            ('action-back-stacked', 0, 'the hand-made Back geometry'),
            ('#adb5bd', 0, 'the off-token grey'),
            ('border-radius: 10px', 0, 'the tile radius literal'),
            ('border-radius: 12px', 0, 'the slab radius literal'),
            ('border-radius: 8px', 0, 'the menu radius literal - base '
             'owns that rule now'),
            ('container-fluid', 0, 'the full-width container'),
            ('class="section-title"', 0, 'the private section heading'),
            ('opacity: 0.45', 0, 'the landing dim'),
            ('opacity: 0.5', 0, 'the disabled-tile dim'),
            ('clicked', 0, 'the click animation, rule and script'),
            ('selectorCard', 0, 'the old selector handle'),
            ('<a class="dash-card" data-box-type="', TILES, 'the live tiles'),
            ('dash-card dash-card-disabled', TWINS, 'the twins'),
            ('class="page-action-buttons"', 1, 'the house bar'),
            ('id="choosePropertyBtn"', 1, 'the real Choose Property button'),
            ('<span class="action-back-label"> Back</span>', 1,
             'the house back label'),
            ('class="alv-card alv-chosen-property"', 1, 'the house card'),
            ('form-section-title', SEC_N, 'base section heading'),
            ('opacity: 0.75', 1, 'the measured dim'),
            ('var(--alv-ink-soft)', 2, 'the switched-off tile ink'),
            ('var(--alv-ink-faint)', 1, 'the chevron'),
            ('var(--alv-radius-sm)', 1, 'the tile radius token'),
            ('a.dash-card[href]', 4, 'the armed-only rules'),
            ('setAttribute(\'href\'', 1, 'the one place a tile gains a '
             'destination'),
            ('<button type="button" class="property-picker-item"', 1,
             'the picker row as a button')):
        got = code.count(lit)
        if got != want:
            refuse('%s: after the edit %r appears %d time(s) in CODE, '
                   'expected %d (%s)' % (PAGE, lit[:58], got, want, what))

    # A CONTROL THAT CAN FAIL. The twelve twins must NOT have become
    # anchors. A replace on `class="dash-card"` alone would have taken
    # all twenty-four, and the result renders identically - it is only
    # wrong for the users who have no permission, which is the set of
    # users least likely to be the one testing it.
    if '<a class="dash-card dash-card-disabled"' in code:
        refuse('a permission-denied twin became an anchor - it must stay a '
               'div, because it is not a link')
    if code.count('<div class="dash-card dash-card-disabled"') != TWINS:
        refuse('the %d twins are no longer %d plain divs' % (TWINS, TWINS))

    # AND THE OTHER HALF OF code_only: the record must SURVIVE. The
    # round deletes twenty-one declarations and a whole component; the
    # comments naming them are the only thing that will tell the next
    # reader what this page used to be. A stripper with no such control
    # is one regex away from a round that silently explains nothing.
    for word in ('dashboard-side-actions', 'Click to choose',
                 '.dash-card.clicked', '#adb5bd', 'container-fluid',
                 'property-selector-card'):
        if word not in npage:
            refuse('the record of %r did not survive - this round deletes '
                   'it and the comment that says so is the only thing left '
                   'explaining the page' % word)

    # THE RULE COUNT, MEASURED NOT GUESSED.
    nrules = css_rules(npage)
    print('DB-5  local rules %d -> %d' % (LOCAL_RULES_WAS, len(nrules)))

    # ---------------------------------------------------------------- 4
    # REGISTRATION. A round that is not on the gate is a round that
    # will be undone by the next person who runs the gate.
    tree = read(os.path.join(root, TREE))
    t_anchor = "    'test_help_label.py',\n]"
    once(tree, t_anchor, TREE)
    ntree = tree.replace(
        t_anchor,
        "    'test_help_label.py',\n"
        "    # DB-5, 12 Oct 2026 - the Property Dashboard onto house\n"
        "    # standards, and the round that found the page could not be\n"
        "    # used from a keyboard at all.\n"
        "    'test_dash_std.py',\n]", 1)

    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_pileases',\n"
    once(rounds, r_anchor, ROUNDS)
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(os.path.join(root, PS1))
    p_anchor = "    'test_pi_leases.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor, "    'test_pi_leases.py',\n    '%s'\n)" % SUITE, 1)

    once(nps, GT_SENTINEL_AFTER, PS1)
    nps = nps.replace(
        GT_SENTINEL_AFTER,
        "    # -------------------------------------------- DB-5, 12 Oct 2026\n"
        "    # The landing dim. 0.45 put the tile label at 2.54:1 and the\n"
        "    # accent icon at 1.91:1 on the page you arrive at, and no\n"
        "    # contrast gate in this system reads opacity, so it passed\n"
        "    # every sweep. 0.75 is the lowest dim at which the icon still\n"
        "    # clears 3.0:1. Its return is the regression.\n"
        "    #\n"
        "    # IT DOES NOT SAY 'pointer-events: none'. The first version of\n"
        "    # this row did, and the TWIN keeps that declaration on purpose\n"
        "    # - so the sentinel asserted the absence of a string that must\n"
        "    # be present, and took ten suites down with it. A control that\n"
        "    # cannot pass is as bad as one that cannot fail. The grid's own\n"
        "    # pointer-events is guarded in test_dash_std section 4, where\n"
        "    # the CSS can be split and the two rules told apart.\n"
        "    @{ File = 'pages\\templates\\property_management_dashboard.html'; "
        "Text = 'opacity: 0.45'; "
        "What = 'the landing dim stays at the measured 0.75'; "
        "Absent = $true; Code = $true }\n"
        + GT_SENTINEL_AFTER, 1)

    # A SENTINEL. The last row of a PowerShell array literal carries no
    # comma - E-10 shipped one that did and the gate would not parse, so
    # the structure is read back rather than assumed. And the first
    # version of THAT guard demanded a comma on every row and refused on
    # three pre-existing ones, because a newline separates elements
    # inside @() just as a comma does. A rule invented rather than
    # measured, twice in one round.
    blk = nps[nps.index('$sentinels = @('):]
    blk = blk[:blk.index('\n)\n')]
    body = [l.rstrip() for l in blk.split('\n')
            if l.strip() and not l.strip().startswith('#')]
    if body[-1].endswith(','):
        refuse('%s: the last thing in $sentinels ends in a comma - %r. That '
               'is a ParserError before the closing paren, and the script '
               'will not run AT ALL.' % (PS1, body[-1][-40:]))

    co = read(os.path.join(root, CO))
    c_was = "ok(len(aliased) == %d," % ALIAS_WAS
    once(co, c_was, CO)
    nco = co.replace(c_was, "ok(len(aliased) == %d," % ALIAS_NOW, 1)
    # THE COMMA STAYS WHERE IT IS. The first version of this replaced
    # the string expression and left the original trailing comma glued
    # to the end of a comment line - a SyntaxError in the suite that
    # catches other people's syntax errors. The anchor now includes the
    # comma, so there is nothing to misplace.
    c_txt = ("'%d file(s) alias it - 22 patchers and 23 suites'"
             " % len(aliased),")
    once(nco, c_txt, CO)
    nco = nco.replace(
        c_txt,
        "'%d file(s) alias it - 23 patchers and 24 suites' % len(aliased),"
        "   # DB-5, 12 Oct 2026 - two more, and both were a DEFINITION"
        " first: this suite caught them, which is what it is for."
        "   # (was 45, 22 and 23)", 1)

    hl = read(os.path.join(root, HLP))
    for was, now, why in (
            ('LABELS_TOTAL = %d' % LABELS_WAS,
             'LABELS_TOTAL = %d' % LABELS_NOW,
             'the dashboard Back gains the house label'),
            ('HELP_TOTAL = %d' % HELPS_WAS,
             'HELP_TOTAL = %d' % HELPS_NOW,
             'and a Help secondary joins the bar')):
        once(hl, was, HLP)
        hl = hl.replace(
            was, '%s   # DB-5, 12 Oct 2026 - %s   # (was %s)'
            % (now, why, was.split('= ')[1]), 1)
    nhl = hl

    pc = read(os.path.join(root, PC))
    p_was = 'EXPECT_PAIRS = %d' % PAIRS_WAS
    once(pc, p_was, PC)
    npc = pc.replace(
        p_was,
        'EXPECT_PAIRS = %d   # DB-5, 12 Oct 2026 - four rules that set\n'
        '# both a background and a colour went with the teal slab and the\n'
        '# side menu   # (was %d)' % (PAIRS_NOW, PAIRS_WAS), 1)

    dr = read(os.path.join(root, DR))
    for name in ('test_bar_height.py', 'test_pair_contrast.py'):
        d_was = "read(os.path.join(ROOT, '%s'))" % name
        once(dr, d_was, DR)
        dr = dr.replace(
            d_was,
            "alv_rounds.as_left_by(\n"
            "    os.path.join(ROOT, '%s'), SUFFIX, read)" % name, 1)
    ndr = dr.replace(
        "# AND THE TWO CENSUSES THE TWELVE WALK INTO, found by the sweep.",
        "# AND THE TWO CENSUSES THE TWELVE WALK INTO, found by the sweep.\n"
        "# DB-5, 12 Oct 2026 - AS E-10 LEFT THEM, not as they stand today.\n"
        "# These two lines read the live files, so the first later round to\n"
        "# re-pin either census made this suite report that E-10 had done\n"
        "# something it had not. DB-5 was that round. A suite asking about\n"
        "# its OWN round must never read the live file - lesson 40, and the\n"
        "# three checks below now pass for every round after this one too.",
        1)
    if ndr == dr:
        refuse('%s: the census comment anchor is not there' % DR)

    bh = read(os.path.join(root, BH))
    b_was = 'N_BAR, N_ROW, N_MODAL = %d, 110, 98' % BAR_WAS
    once(bh, b_was, BH)
    nbh = bh.replace(
        b_was,
        'N_BAR, N_ROW, N_MODAL = %d, 110, 98   # DB-5, 12 Oct 2026 - the\n'
        '# dashboard four joined the bar   # (was %d)'
        % (BAR_NOW, BAR_WAS), 1)
    l_was = 'N_LOOSE, N_LOOSE_H = %d, %d' % (LOOSE_WAS, LOOSEH_WAS)
    once(nbh, l_was, BH)
    nbh = nbh.replace(
        l_was,
        'N_LOOSE, N_LOOSE_H = %d, %d   # DB-5 - the side column left the\n'
        '# loose set, and the two heights it invented went with it\n'
        '# (was %d and %d)'
        % (LOOSE_NOW, LOOSEH_NOW, LOOSE_WAS, LOOSEH_WAS), 1)

    wd = read(os.path.join(root, WD))
    w_was = 'CONVERTED_N = %d' % CONVERTED_WAS
    once(wd, w_was, WD)
    nwd = wd.replace(
        w_was,
        'CONVERTED_N = %d   # DB-5, 12 Oct 2026 - this round own suite; no '
        'existing\n# suite was converted, so the ceiling does not move   '
        '# (was %d)' % (CONVERTED_NOW, CONVERTED_WAS), 1)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('')
        print('DB-5  check only - nothing written')
        print('DB-5  would put the Property Dashboard on the house action')
        print('DB-5  bar - of %d pages carrying a More wrapper, %d already'
              % (MORE_PAGES, MORE_IN_BAR))
        print('DB-5  do, and this is the one that does not')
        print('DB-5  would delete %d .dashboard-side-actions rules and the'
              % SIDE_RULES)
        print('DB-5  teal slab, and put the chosen property on base .alv-card')
        print('DB-5  would make the %d tiles real links and the picker rows'
              % TILES)
        print('DB-5  real buttons - THE PAGE CANNOT BE USED FROM A KEYBOARD')
        print('DB-5  today: the selector, the tiles and the picker rows are')
        print('DB-5  divs with a click listener and no key handling at all')
        print('DB-5  would take the landing dim %s -> %s, the lowest value'
              % (DIM_WAS, DIM_NOW))
        print('DB-5  at which the accent icon still clears 3.0:1')
        print('DB-5  would take the switched-off tile from 1.33:1 to 4.97:1')
        print('DB-5  CONVERTED %d -> %d, WAITING and the ceiling unchanged'
              % (CONVERTED_WAS, CONVERTED_NOW))
        return 0

    for p, txt in [(page_p, npage),
                   (os.path.join(root, TREE), ntree),
                   (os.path.join(root, ROUNDS), nrounds),
                   (os.path.join(root, WD), nwd),
                   (os.path.join(root, CO), nco),
                   (os.path.join(root, BH), nbh),
                   (os.path.join(root, DR), ndr),
                   (os.path.join(root, HLP), nhl),
                   (os.path.join(root, PC), npc),
                   (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, txt)

    print('')
    print('DB-5  the Property Dashboard is on the house action bar, the')
    print('DB-5  shape %s has. %d local rules -> %d.'
          % (REFERENCE, LOCAL_RULES_WAS, len(nrules)))
    print('DB-5  THE PAGE CAN BE USED FROM A KEYBOARD NOW. Before this')
    print('DB-5  round the selector, all %d tiles and every row in the'
          % TILES)
    print('DB-5  picker were divs with a click listener and nothing else -')
    print('DB-5  no role, no tabindex, no key handler anywhere in the')
    print('DB-5  script. Tab through it and you reached the hamburger and')
    print('DB-5  the Back link, and that was all.')
    print('DB-5  The landing dim is %s, not %s - the lowest value at which'
          % (DIM_NOW, DIM_WAS))
    print('DB-5  the accent icon clears 3.0:1 (3.14 at .75, 2.90 at .70).')
    print('DB-5  A switched-off tile reads 4.97:1, not 1.33:1.')
    print('DB-5  Neither test_more_css nor test_last_menus is touched:')
    print('DB-5  both read this page through as_left_by and both have')
    print('DB-5  been reading history since .bak_msgbar. Their recorded')
    print('DB-5  reasons are measurements of their own moment.')
    print('DB-5  CONVERTED %d -> %d.' % (CONVERTED_WAS, CONVERTED_NOW))
    print('DB-5  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
