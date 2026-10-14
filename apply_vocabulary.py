# -*- coding: utf-8 -*-
"""apply_vocabulary.py - round VC-1, 14 Oct 2026.

THE GATE NOW ASKS EVERY PAGE. IT STILL DOES NOT ASK EVERY BUTTON.

RS-1b widened the drift gate's PAGE scope from 117 to 142 and said in its
own suite that it had not widened the VOCABULARY. This is that half.

FIVE HOLES, ALL MEASURED BEFORE THE ROUND WAS WRITTEN
------------------------------------------------------
1. A TAG, NOT A CLASS. `BTN` matched <a|button|span>. Three controls are
   <label> - a label wrapping a hidden <input type="file">, which is how
   you style a file picker - and every census in this project has been
   blind to them since the first one:

       property_assets   Take Photo    btn btn-outline-info
       edit_asset        Take Photo    btn btn-outline-info
       my_profile        Upload Photo  btn btn-sm btn-outline-primary   3.98:1

   TWO OF THE THREE ARE PROPERTY-SIDE. `btn-camera-capture` is
   display:none on desktop and revealed by a mobile media query, which is
   why they never caught an eye at a laptop. Adding `label` to BTN
   surfaces exactly these three and nothing else.

2. TWO BOOTSTRAP COLOURS THE LIST OMITTED. BOOTSTRAP carried six of
   Bootstrap's eight outline variants. The note beside that list already
   says why it matters - "Leaving them off the list did not make them out
   of scope, it made them INVISIBLE" - and two shades further on it
   happened again: `btn-outline-light` on two ingredient_families icons.
   `btn-outline-dark` is unused today and is listed anyway, or the hole
   reopens the day somebody reaches for it. `btn-link` is listed as a
   COLOUR - Demetri's call - because it sets Bootstrap blue text as well
   as removing the border.

3. A HOUSE CLASS THE LIST OMITTED TOO, and this one was Demetri's own
   decision. `action-field-add` was in neither TONES nor POSITION nor
   MISNAMED, so property_assets' three + buttons - the ones he asked to
   be teal on 30 Sep - were invisible to the report. And naming it is not
   enough; measured first:

       plan_bar would give it : action-secondary
       rebuild would write    : btn action-secondary action-field-add

   So it gets the `action-filter` treatment: a name in POSITION AND a
   skip_reason, because base.html styles it directly and it takes no
   tone. action-filter's own note records the same lesson from the other
   side - without the name, eight correct Filter buttons were reported as
   drift. Here, without the name, three correct buttons vanished.

4. A STRUCTURAL HOLE. `_scan` dropped a button with no Bootstrap colour
   and no house class BEFORE it asked decided_tone, so a wrapper with a
   recorded decision could not reach one. connectivity_error's TRY AGAIN
   is `class="btn"` inside `.button-group`, and DECIDED['button-group']
   is [('go back', B), ('*', P)] - it should be the primary and the
   report has never mentioned it.

5. AND WHAT IS LEFT IS COUNTED RATHER THAN DROPPED. A button whose
   colour comes from page CSS, an inline style or JavaScript is not
   drift - base.html owns nothing on it - but silently skipping it is how
   every blind spot in this file started. There is a PAINTED bucket now,
   printed with a count. It does not fire --strict, because a button with
   no colour class is not what the gate's sentence is about; the SUITE
   pins the count instead, which is this project's usual bargain.

WHAT THE SEVENTEEN TURNED OUT TO BE
------------------------------------
    3   property_assets      correct house buttons, class unlisted   -> hole 3
    2   ingredient_families  btn-outline-light, 2.97:1 on green      -> row actions
    1   pantry_staples       btn-link text-danger icon Remove        -> row actions
    1   create_meal_plan     Favourites, painted by JavaScript       -> aria-pressed
    1   connectivity_error   Try Again, class="btn"                  -> hole 4
    5   customer_invoice_form  btn-delete/-duplicate/-approve/-send/-unapprove
    3   physical_invoice_edit  btn-delete/-approve/-unapprove
    1   meal_plan_shopping_list  share-whatsapp

The last NINE are already on house tokens - --alv-bad, --alv-accent,
--alv-good, --alv-warn, --alv-on-accent, with a 44px min-height. They are
not drift and they are not retoned here. They go on the register with a
reason, so they stop being invisible. WHETHER A STATUS ROW SHOULD BE FIVE
SOLID FILLS IS A DESIGN QUESTION AND NOT THIS ROUND'S.

A CONTRAST DEFECT THIS ROUND FOUND BY RENDERING
------------------------------------------------
ingredient_families' two icons sit in a card header that is
`bg-success text-white` - solid Bootstrap green - which is why somebody
reached for btn-outline-light. Rendered on that green:

    today, btn-sm btn-outline-light          2.97:1   FAILS
    action-secondary                        12.95:1
    row-actions + icon-edit / icon-delete    5.17:1

So they are not merely inconsistent. They become the house row-action
pair, and the argument is not aesthetic: an edit pencil and a trash
beside the record they act on is what .icon-action-btn exists for;
`.row-actions` in base is `inline-flex; gap: 6px`, which is IDENTICAL to
the inline style it replaces, so the layout does not move and an inline
style goes away; icon-action-btn is explicitly 34x34 where today's pair
have no size of their own; and the row-action guard then owns their
ORDER, which FAMILY already sorts CHANGE before DESTROY - the order the
page is already in.

RECORDED, NOT FIXED
-------------------
The green card header itself. bg-success / bg-info / bg-danger /
bg-warning appear 14 times on 10 pages - wcim_results 3, pantry_staples
2, projects/projects_detail 2 and seven others. They are Bootstrap
colours on PANELS rather than buttons, so no button census has ever been
asked about them. Bigger surface than the buttons were, and its own
round.

Also outside BTN by class and correct today: 62 `action-more-item` menu
rows and 27 `admin-btn btn-alivente` Administration tiles. Neither
carries a `btn` token, so BTN never reaches them.

See test_vocabulary.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_vocab'
SUITE = 'test_vocabulary.py'
DRIFT = 'Show-ButtonDrift.py'
RA = 'alv_rowactions.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

N_LABELS = 3
N_TONED = 5            # the 3 labels, Try Again, and a WhatsApp tile
N_ROW_ACTIONS = 3      # ingredient_families x2, pantry_staples x1
N_REGISTER = 8         # the invoice status rows, named not retoned
N_SILENCED = 8         # house-toned buttons a LEAVE wrapper hides
N_PAINTED_WAS, N_PAINTED_NOW = 17, 0

CONVERTED_WAS, CONVERTED_NOW = 75, 76
ALIAS_WAS, ALIAS_NOW = 61, 63
ALIAS_P_WAS, ALIAS_P_NOW = 30, 31
ALIAS_S_WAS, ALIAS_S_NOW = 31, 32

# ---------------------------------------------------------------------------
# Show-ButtonDrift.py - the four holes
# ---------------------------------------------------------------------------
BTN_WAS = """BTN = re.compile(r'<(a|button|span)\\b[^>]*class="([^"]*(?:(?<![-\\w])btn(?![-\\w])'"""

BTN_NOW = """# AND <label>, SINCE VC-1, 14 Oct 2026 - AND IT IS A TAG, NOT A CLASS.
#
# Three controls in this application are a <label> wrapping a hidden
# <input type="file">, which is how a file picker is styled, and every
# census here has been blind to them since the first one:
#
#     property_assets   Take Photo    btn btn-outline-info
#     edit_asset        Take Photo    btn btn-outline-info
#     my_profile        Upload Photo  btn btn-sm btn-outline-primary  3.98:1
#
# TWO OF THE THREE ARE PROPERTY-SIDE, so this was not a recipe-side
# leftover; and btn-camera-capture is display:none on desktop, revealed
# by a mobile media query, which is why they never caught an eye at a
# laptop. Measured before widening: `label` surfaces exactly these three
# and nothing else, across both template roots.
#
# <input type="submit"> would be the next tag to ask about and there are
# none carrying a btn token - measured, not assumed.
BTN = re.compile(r'<(a|button|span|label)\\b[^>]*class="([^"]*(?:(?<![-\\w])btn(?![-\\w])'"""

BOOT_WAS = """             'btn-outline-success', 'btn-outline-warning')"""

BOOT_NOW = """             'btn-outline-success', 'btn-outline-warning',
             # VC-1, 14 Oct 2026 - SIX OF BOOTSTRAP'S EIGHT IS NOT THE
             # LIST. The note above says exactly why this matters and it
             # happened again two shades along: ingredient_families
             # carried two btn-outline-light icons, at 2.97:1 on a green
             # card header, and no census in this project could see
             # them. btn-outline-dark is unused today and is listed
             # anyway - an unused name on this list costs nothing, and
             # leaving it off is what reopens the hole.
             'btn-outline-light', 'btn-outline-dark',
             # AND btn-link IS A COLOUR HERE, which Demetri decided. It
             # sets Bootstrap blue text as well as removing the border,
             # so a page using it is choosing a colour whatever else it
             # is doing. One button today, on pantry_staples, and VC-1
             # gives it to the row-action guard.
             'btn-link')"""

POS_WAS = """            'action-filter')"""

POS_NOW = """            'action-filter',
            # VC-1, 14 Oct 2026 - AND action-field-add, WHICH WAS ON NO
            # LIST AT ALL. base.html styles it directly: paper fill,
            # teal border, teal ink, filling on hover. It is Demetri's
            # own decision of 30 Sep - "why are these + buttons in
            # green, they should be in teal" - and because the name was
            # in neither TONES nor POSITION, HOUSE did not contain it
            # and property_assets' three correct buttons were invisible
            # to this report for a fortnight.
            #
            # IT NEEDS THE skip_reason BELOW AS WELL AS THIS LINE, and
            # that was measured rather than assumed: with only the name,
            # plan_bar hands it action-secondary and rebuild writes
            # `btn action-secondary action-field-add` - three correct
            # buttons reported as drift, which is precisely what
            # action-filter's note above describes happening to eight.
            'action-field-add')"""

SKIP_WAS = """        return 'the filter toggle - base styles .action-filter directly'
    return None"""

SKIP_NOW = """        return 'the filter toggle - base styles .action-filter directly'
    if 'action-field-add' in cls.split():
        # VC-1, 14 Oct 2026. Third time, same shape: base.html styles
        # this one directly too - a small add control welded to a field,
        # paper fill and a teal edge - so it takes no tone and must not
        # be handed one. Without this line the three property_assets
        # buttons go from invisible to wrongly reported, which is a
        # different fault and not an improvement.
        return 'a small add control welded to a field - base styles it'
    return None"""

# ---------------------------------------------------------------------------
# _scan - ask the register before giving up, and COUNT what is left
# ---------------------------------------------------------------------------
SCAN_WAS = """        cls = b.group(2)
        names = cls.split()
        boot = [c for c in names if c in BOOTSTRAP]
        has_house = any(c in HOUSE for c in names)
        if not boot and not has_house:
            continue
        open_tag = b.group(0)[:b.group(0).index('>') + 1]
        lab = label_of(b.group(3))
        wrap = innermost_wrapper(m, b.start())
        why = skip_reason(cls)

        if in_table(m, b.start()):
            why = why or 'a row action inside a table'
        tone, leave_why = decided_tone(wrap, lab)
        if leave_why:
            why = why or leave_why

        if why:"""

SCAN_NOW = """        cls = b.group(2)
        names = cls.split()
        boot = [c for c in names if c in BOOTSTRAP]
        has_house = any(c in HOUSE for c in names)
        open_tag = b.group(0)[:b.group(0).index('>') + 1]
        lab = label_of(b.group(3))
        wrap = innermost_wrapper(m, b.start())
        why = skip_reason(cls)

        if in_table(m, b.start()):
            why = why or 'a row action inside a table'
        tone, leave_why = decided_tone(wrap, lab)
        if leave_why:
            why = why or leave_why

        # ASK THE REGISTER BEFORE GIVING UP - VC-1, 14 Oct 2026.
        #
        # The drop below used to sit ABOVE these four lines, so a button
        # with no Bootstrap colour and no house class was gone before
        # anyone asked whether its wrapper had a decision on it.
        # connectivity_error's TRY AGAIN is `class="btn"` inside
        # .button-group, and DECIDED['button-group'] says the non-Back
        # control there is the primary. It should have been a solid
        # primary and this report has never once mentioned it.
        #
        # AND WHAT IS STILL LEFT IS COUNTED, NOT DROPPED. A button whose
        # colour comes from page CSS, an inline style or JavaScript is
        # not drift - base.html owns nothing on it, so there is nothing
        # for it to disagree with - but silently skipping a whole
        # category is how every blind spot in this file began. It gets a
        # bucket and a printed count; it does not fire --strict, because
        # a button with no colour class is not what the gate's sentence
        # is about. test_vocabulary.py pins the number instead.
        if not boot and not has_house and tone is None and not why:
            hits.append(('PAINTED', lab, boot, cls, cls,
                         b.start(), b.start() + len(open_tag), None))
            continue

        if why:"""

# ---------------------------------------------------------------------------
# main() - the bucket has to be printed, or it is the old hole with a name
# ---------------------------------------------------------------------------
MAIN_LOOP_WAS = """    rows = []
    skipped_n = collections.Counter()
    unclassified = []"""

MAIN_LOOP_NOW = """    rows = []
    skipped_n = collections.Counter()
    unclassified = []
    painted = []            # VC-1: colour from page CSS, inline style or JS"""

MAIN_COUNT_WAS = """            if x[7]:
                skipped_n[x[7]] += 1
            elif x[0] == 'UNCLASSIFIED':
                unclassified.append((f, x[1], x[3]))"""

MAIN_COUNT_NOW = """            if x[7]:
                skipped_n[x[7]] += 1
            elif x[0] == 'PAINTED':
                # VC-1, 14 Oct 2026. Not drift, not a decision, and no
                # longer dropped on the floor either.
                painted.append((f, x[1], x[3]))
            elif x[0] == 'UNCLASSIFIED':
                unclassified.append((f, x[1], x[3]))"""

MAIN_CLEAN_WAS = """    if not rows and not unclassified:
        print('  Nothing drifting, and nothing undecided.')
        print('  %d button(s) are deliberately left alone:' % sum(skipped_n.values()))
        for why, n in skipped_n.most_common():
            print('     %-52s %3d' % (why, n))
        print_double_bars(dbl)"""

MAIN_CLEAN_NOW = """    if not rows and not unclassified:
        print('  Nothing drifting, and nothing undecided.')
        print('  %d button(s) are deliberately left alone:' % sum(skipped_n.values()))
        for why, n in skipped_n.most_common():
            print('     %-52s %3d' % (why, n))
        print_painted(painted)
        print_double_bars(dbl)"""

MAIN_UNCL_WAS = """    if unclassified:
        print('')"""

MAIN_UNCL_NOW = """    print_painted(painted)

    if unclassified:
        print('')"""

PRINT_PAINTED_ANCHOR = """def print_double_bars(rows):"""

PRINT_PAINTED = '''def print_painted(rows):
    """Buttons whose colour comes from somewhere this tool cannot name.

    VC-1, 14 Oct 2026. NOT DRIFT: base.html owns nothing on a button
    with no Bootstrap colour and no house class, so there is nothing for
    it to disagree with. But seventeen of these existed when VC-1 was
    written and every one of them was dropped in silence - three were
    CORRECT house buttons whose class was on no list, one was a toggle
    painted by JavaScript, and one should have been a solid primary by a
    decision already on the register.

    Printed with a count, and not gated: --strict firing on this would
    fail a push over a button nobody has claimed base owns. The suite
    pins the number, which is where a count belongs.
    """
    print('')
    if not rows:
        print('  No button takes its colour from page CSS, an inline style')
        print('  or JavaScript. [VC-1]')
        return
    print('  %d BUTTON(S) PAINTED SOMEWHERE THIS TOOL CANNOT NAME'
          % len(rows))
    print('  No Bootstrap colour and no house class, so nothing here is')
    print('  drift - but nothing here is on record either.')
    for f, lab, cls in rows[:14]:
        print('     %-40s %-22s %s' % (f[:40], lab[:22], cls[:30]))
    if len(rows) > 14:
        print('     ... and %d more' % (len(rows) - 14))


def print_double_bars(rows):'''

# ---------------------------------------------------------------------------
# the markup - four tones
# ---------------------------------------------------------------------------
# .photo-upload-controls is a flex column and the file input beside it is
# hidden on a phone, so Take Photo is the only visible control there. Demetri
# decided action-secondary rather than action-primary: the page's verb is Save,
# and two solid teal buttons on one phone screen is the thing a single primary
# per page exists to prevent.
TONES = (
    ('edit_asset.html',
     '<label class="btn btn-outline-info btn-camera-capture">',
     '<label class="btn action-secondary btn-camera-capture">',
     'Take Photo - a file-input label, mobile only'),
    ('property_assets.html',
     '<label class="btn btn-outline-info btn-camera-capture">',
     '<label class="btn action-secondary btn-camera-capture">',
     'Take Photo - a file-input label, mobile only'),
    ('my_profile.html',
     '<label class="btn btn-sm btn-outline-primary" style="cursor:pointer;">',
     '<label class="btn action-secondary btn-sm" style="cursor:pointer;">',
     'Upload Photo - and a contrast repair, 3.98 to 12.95'),
    ('meal_plan_shopping_list.html',
     '<button onclick="shareToWhatsApp()" class="btn share-btn '
     'share-whatsapp">',
     '<button onclick="shareToWhatsApp()" class="btn action-secondary '
     'share-btn share-whatsapp">',
     'WhatsApp - its three siblings in that grid are already house'),
    ('error_pages/connectivity_error.html',
     '<button onclick="retryConnection()" class="btn" id="retryBtn">',
     '<button onclick="retryConnection()" class="btn action-primary" '
     'id="retryBtn">',
     'Try Again - the primary DECIDED said it was all along'),
)

# ---------------------------------------------------------------------------
# the markup - three controls that become row actions
# ---------------------------------------------------------------------------
# ingredient_families: an edit pencil and a trash on the card they act on.
# `.row-actions` is `inline-flex; gap: 6px` in base, which is identical to the
# inline style it replaces, so the layout does not move by a pixel.
FAM_WRAP_WAS = """<div style="display: flex; gap: 6px;">"""
FAM_WRAP_NOW = """<div class="row-actions">"""

FAM_EDIT_WAS = """<button type="button" class="btn btn-sm btn-outline-light family-edit-btn\""""
FAM_EDIT_NOW = """<button type="button" class="icon-action-btn icon-edit family-edit-btn\""""

FAM_DEL_WAS = """<button type="submit" class="btn btn-sm btn-outline-light" title="Delete family">"""
FAM_DEL_NOW = """<button type="submit" class="icon-action-btn icon-delete" title="Delete family">"""

# AND THE GLYPH MOVES TOO, which the row-action guard insisted on and I
# had not planned. alv_rowactions states "A CLASS CARRIES ONE PICTURE",
# and every other .icon-delete in this application is fa-trash; this one
# was fa-times, the Bootstrap chip-remove idiom. Putting icon-delete on a
# fa-times made the guard report one name with two pictures - correctly -
# so the cross becomes a bin, like the other five. A VISIBLE CHANGE, and
# the only one in this round nobody asked for: the guard did.
PANTRY_WAS = """<button type="submit" class="btn btn-sm btn-link text-danger p-0" title="Remove">
                      <i class="fas fa-times"></i>"""
PANTRY_NOW = """<button type="submit" class="icon-action-btn icon-delete" title="Remove">
                      <i class="fas fa-trash"></i>"""

# ---------------------------------------------------------------------------
# the markup - the toggle that was painted by JavaScript
# ---------------------------------------------------------------------------
# B-1 fixed the identical control on recipe_management on 2 Oct and base.html
# already answers it: `.btn.action-secondary[aria-pressed="true"]`, the same
# three tokens as `.action-filter[aria-pressed="true"]`. So no tone is
# invented and no literal is added to base.
FAV_WAS = """<button class="btn w-100" id="favouritesToggleBtn" onclick="toggleFavouritesFilter()"
                                    style="border: 2px solid var(--alv-line); background: white; color: var(--alv-neutral);">"""

FAV_NOW = """<button class="btn action-secondary w-100" id="favouritesToggleBtn"
                                    onclick="toggleFavouritesFilter()"
                                    aria-pressed="false">"""

FAV_JS_WAS = """function toggleFavouritesFilter() {
    showFavouritesOnly = !showFavouritesOnly;
    const btn = document.getElementById('favouritesToggleBtn');
    if (showFavouritesOnly) {
        btn.style.background = 'var(--alv-bad)';
        btn.style.borderColor = '#e74c3c';
        btn.style.color = 'white';
    } else {
        btn.style.background = 'white';
        btn.style.borderColor = 'var(--alv-line)';
        btn.style.color = 'var(--alv-neutral)';
    }
    searchRecipesInSelector();
}"""

FAV_JS_NOW = """function toggleFavouritesFilter() {
    // VC-1, 14 Oct 2026 - THE STATE IS aria-pressed, NOT A STYLE.
    //
    // This used to write background, borderColor and color onto the
    // element, which is why no button census in this project could see
    // the control at all: no Bootstrap colour, no house class, its whole
    // appearance in an inline style and its state in JavaScript.
    //
    // B-1 fixed the identical control on recipe_management on 2 Oct and
    // base.html already answers it - the same three tokens as
    // .action-filter when pressed - so nothing is invented here, and a
    // screen reader is told as well.
    showFavouritesOnly = !showFavouritesOnly;
    const btn = document.getElementById('favouritesToggleBtn');
    if (btn) { btn.setAttribute('aria-pressed', showFavouritesOnly ? 'true' : 'false'); }
    searchRecipesInSelector();
}"""

FAV_RESET_WAS = """    const favBtn = document.getElementById('favouritesToggleBtn');
    if (favBtn) {
        favBtn.style.background = 'white';
        favBtn.style.borderColor = 'var(--alv-line)';
        favBtn.style.color = 'var(--alv-neutral)';
    }"""

FAV_RESET_NOW = """    const favBtn = document.getElementById('favouritesToggleBtn');
    if (favBtn) { favBtn.setAttribute('aria-pressed', 'false'); }"""

# AND A THIRD SITE, which the SUITE found and I had not. clearRecipeFilters
# resets the same toggle and painted it the same way, under a different
# local name. Three places wrote the colour of one button; this is why the
# claim in test_vocabulary is "no JavaScript paints it any more" asked of
# the whole file rather than of the handler I happened to be looking at.
FAV_CLEAR_WAS = """    const btn = document.getElementById('favouritesToggleBtn');
    if (btn) {
        btn.style.background = 'white';
        btn.style.borderColor = 'var(--alv-line)';
        btn.style.color = 'var(--alv-neutral)';
    }"""

FAV_CLEAR_NOW = """    const btn = document.getElementById('favouritesToggleBtn');
    if (btn) { btn.setAttribute('aria-pressed', 'false'); }"""

# ---------------------------------------------------------------------------
# test_bar_height.py - three controls became VISIBLE to a height census
# ---------------------------------------------------------------------------
# D-1's suite does NOT use Show-ButtonDrift's BTN. It queries the DOM for
# .action-primary, .action-secondary, .action-back, .action-filter,
# .action-more-btn and .icon-action-btn, and skips anything with no client
# rects. So the moment VC-1 put a house class on three controls that had
# none, that census grew - and D-1's pinned numbers caught it, which is
# exactly what they are for.
#
# MEASURED, not inferred, with D-1's own renderer and selector:
#
#     property_assets  Take Photo    a modal   35px   -> a named stray
#     edit_asset       Take Photo    a card    35px   -> a NEW height
#     my_profile       Upload Photo  a card    31px   -> an existing one
#
# The 35px modal control is NAMED as a stray rather than levelled: it is
# the mobile-only camera label, and D-1's note beside STRAYS is that a
# stray wants a page-by-page look rather than one number. Levelling a
# control that only exists on a phone, from a census taken at 1280px,
# would be the worse answer.
BH = 'test_bar_height.py'

BH_PINS_WAS = """N_BAR, N_ROW, N_MODAL = 268, 110, 98   # DB-5, 12 Oct 2026 - the"""
BH_PINS_NOW = """N_BAR, N_ROW, N_MODAL = 268, 110, 99   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the"""

BH_LOOSE_WAS = """N_LOOSE, N_LOOSE_H = 80, 10   # DB-5 - the side column left the"""
BH_LOOSE_NOW = """N_LOOSE, N_LOOSE_H = 81, 11   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the"""

BH_STRAYS_WAS = """STRAYS = {
    ('a table row', 'crs/submission_detail.html'): 1,
    ('a modal', 'finance_valuations_edit.html'): 1,
    ('a modal', 'help_page.html'): 3,
}"""

BH_STRAYS_NOW = """STRAYS = {
    ('a table row', 'crs/submission_detail.html'): 1,
    ('a modal', 'finance_valuations_edit.html'): 1,
    ('a modal', 'help_page.html'): 3,
    # VC-1, 14 Oct 2026 - THE SIXTH, AND IT IS A PHONE CONTROL.
    #
    # property_assets' Take Photo is the <label> wrapping a hidden file
    # input, revealed only by that page's mobile media query. It had no
    # house class until VC-1 gave it action-secondary, so this census
    # could not see it at all; now it can, and at 1280px it renders
    # 35px rather than the modal's 38.
    #
    # NAMED, NOT LEVELLED. The note above says a stray wants a
    # page-by-page look rather than one number, and levelling a control
    # that only exists on a phone, from a measurement taken at desktop
    # width, is the worse of the two answers available.
    ('a modal', 'property_assets.html'): 1,
}"""

# ---------------------------------------------------------------------------
# test_js_buttons.py - E11's suite. THE NINTH OCCURRENCE, instrument again.
# ---------------------------------------------------------------------------
# E11's section 3 prices its own tightening of BTN by comparing the LIVE
# pattern against the one in .bak_jsbtn: 706 hits loose, 704 tight, exactly
# two pages changing. Both halves of that are a SNAPSHOT of what E11 did.
#
# VC-1 changed the live pattern, so `tight` stopped being E11's and the
# comparison measured two rounds at once: 1119 and 721, 58 pages moving.
# A round that does two things cannot say which one moved - F2b's own words
# - and the fix is the one RS-1b made for RS-1a a day ago, one layer down:
# read the TOOL as the round left it. left() is already in that file.
JS = 'test_js_buttons.py'

JS_TIGHT_WAS = """tight = btn_of(read(os.path.join(ROOT, DRIFT)))"""
JS_TIGHT_NOW = """# REPAIRED BY VC-1, 14 Oct 2026 - AND IT WAS READ LIVE.
#
# `tight` is E11's pattern, and E11's pattern is a SNAPSHOT. Read live it
# became VC-1's - which put <label> in the tag list - so this section
# priced two rounds in one number: 706 and 704 came back as 1119 and
# 721, and "exactly 2 pages change" came back as 58.
#
# AND THE PATTERN WAS NOT THE WHOLE OF IT, which the first repair here
# got wrong. Swapping only `tight` back still failed, because the
# numbers below are a snapshot of the TOOL and not just of its regex:
# VC-1 also added two LEAVE entries, a POSITION name and a PAINTED row
# where _scan used to drop a button in silence. Every one of those
# changes the LENGTH of what _scan returns.
#
# So the whole comparison is run against Show-ButtonDrift AS E11 LEFT
# IT, loaded beside the live one out of this process's own SCRATCH
# directory, and handed back the repo's ROOT and TPL because a module
# that finds the templates from its own __file__ would look for them
# next to the copy.
#
# NINTH OCCURRENCE OF THE as_left_by LESSON, and the SECOND about the
# INSTRUMENT rather than the pages - RS-1b made the first, for RS-1a,
# the day before.
def _tool_as_e11_left_it():
    q = os.path.join(SCRATCH, 'show_buttondrift_as_e11_left_it.py')
    with open(q, 'w', encoding='utf-8') as fh:
        fh.write(left(DRIFT))
    sp = importlib.util.spec_from_file_location('_sb_e11', q)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    mod.ROOT, mod.TPL = sb.ROOT, sb.TPL
    return mod


sb_then = _tool_as_e11_left_it()
tight = btn_of(left(DRIFT))"""

JS_PRICE_WAS = """    # PRICED, over the whole application, both ways.
    def scan_hits(rx):
        keep, n = sb.BTN, 0
        sb.BTN = rx
        try:
            for f in wide:
                p = alv_tree.path_of(f)
                raw = read(p)
                sb.JS_REENABLED = sb.js_reenabled_ids(raw)
                n += len(sb._scan(f, sb.markup_of(raw)))
        finally:
            sb.BTN = keep
        return n"""

JS_PRICE_NOW = """    # PRICED, over the whole application, both ways - AND WITH THE TOOL
    # E11 LEFT, not the live one. See the note beside sb_then above: the
    # count is a property of the whole scanner, and VC-1 changed three
    # other things in it.
    def scan_hits(rx):
        keep, n = sb_then.BTN, 0
        sb_then.BTN = rx
        try:
            for f in wide:
                # AND THE PAGES AS E11 LEFT THEM. left_page() is three
                # hundred lines up and this was the one place in the
                # file still reading them live - which is why the count
                # came back 709 and 707 once VC-1 moved three buttons
                # onto .icon-action-btn and off .btn.
                raw = left_page(f)
                sb_then.JS_REENABLED = sb_then.js_reenabled_ids(raw)
                n += len(sb_then._scan(f, sb_then.markup_of(raw)))
        finally:
            sb_then.BTN = keep
        return n"""

JS_ROWS_WAS = """    def rows(rx, f):
        keep = sb.BTN
        sb.BTN = rx
        try:
            raw = read(alv_tree.path_of(f))
            sb.JS_REENABLED = sb.js_reenabled_ids(raw)
            return sb._scan(f, sb.markup_of(raw))
        finally:
            sb.BTN = keep"""

JS_ROWS_NOW = """    def rows(rx, f):
        keep = sb_then.BTN
        sb_then.BTN = rx
        try:
            raw = left_page(f)
            sb_then.JS_REENABLED = sb_then.js_reenabled_ids(raw)
            return sb_then._scan(f, sb_then.markup_of(raw))
        finally:
            sb_then.BTN = keep"""

# ---------------------------------------------------------------------------
# test_cssrules_outside.py - one hard-coded hex left the application
# ---------------------------------------------------------------------------
# VC-1 took the Favourites toggle off inline styles, and one of the three
# JavaScript sites was writing `#e74c3c` - a literal hex, not a token. So
# that suite's census of colour literals inside <script> bodies comes down
# by one, and so does the var-safe subset, because a style-prop write is
# exactly the kind this round's predecessor B-7 called convertible.
#
# THE NUMBERS GO DOWN, WHICH IS WHY THEY ARE BUMPED RATHER THAN RELAXED. A
# pin that only ever loosens asserts nothing.
CSS = 'test_cssrules_outside.py'

CSS_SCRIPT_WAS = """SCRIPT = 149            # colour literals inside <script> bodies"""
CSS_SCRIPT_NOW = """SCRIPT = 148            # colour literals inside <script> bodies   # VC-1, 14 Oct 2026 - create_meal_plan's Favourites toggle no longer writes #e74c3c from JavaScript; it carries aria-pressed and base paints it.   # (was 149)"""

CSS_CTX_WAS = """CTX = {'style-attr': 22, 'style-prop': 9, 'css-text': 0,"""
CSS_CTX_NOW = """CTX = {'style-attr': 22, 'style-prop': 8, 'css-text': 0,   # VC-1 - the hex above was a style-prop write, the var-safe kind   # (style-prop was 9)"""

CSS_SAFE_WAS = """ok(safe == 31,
   '31 of the 149 may become var() - and 118 may not, which is '"""
CSS_SAFE_NOW = """ok(safe == 30,
   '30 of the 148 may become var() - and 118 may not, which is '"""

# ---------------------------------------------------------------------------
# test_neutrals.py - the suite that CHECKS those pins were updated
# ---------------------------------------------------------------------------
# B-5b asserts the TEXT of CR-1's census numbers from inside its own suite,
# with the reason written beside it: "This is the gate B-4's push failed on:
# it moved four of CR-1's census numbers and left them." VC-1 moved three of
# them, so it owns them here as well - which is the check doing exactly its
# job, one round later.
NEU = 'test_neutrals.py'

NEU_WAS = """for want in ('MARKUP_STYLE = 88', 'SCRIPT = 149', 'PAGES = 36',
             "'style-attr': 22", "'style-prop': 9",
             'safe == 31'):"""

NEU_NOW = """# VC-1, 14 Oct 2026 - three of the six moved DOWN by one. The
# Favourites toggle on create_meal_plan was writing #e74c3c from
# JavaScript; it carries aria-pressed now and base.html paints it, so one
# style-prop literal left the application and the var-safe subset lost it
# too. A pin that only ever loosens asserts nothing, which is why these
# are rewritten rather than relaxed.
for want in ('MARKUP_STYLE = 88', 'SCRIPT = 148', 'PAGES = 36',
             "'style-attr': 22", "'style-prop': 8",
             'safe == 30'):"""

# ---------------------------------------------------------------------------
# test_recipe_side_b.py - RS-1b's suite. ITS DEBT, TURNED OVER
# ---------------------------------------------------------------------------
# RS-1b's section 5 wrote down what it had NOT done: seventeen buttons the
# gate could not see, two of them btn-outline-light, and "this round did NOT
# widen the vocabulary". VC-1 is the round that widened it, so those three
# checks are turned over rather than deleted - the same move RS-1b made for
# RS-1a's claim that RS-1b owed it the wider gate, one day later.
#
# A claim allowed to disappear on the day it comes true leaves no record
# that it was ever owed.
RSB = 'test_recipe_side_b.py'

RSB_INV_WAS = """ok(sum(inv.values()) == N_INVISIBLE and len(inv) == N_INVISIBLE_PAGES,
   '%d button(s) in %d page(s) carry neither a listed Bootstrap colour '
   'nor a house class' % (N_INVISIBLE, N_INVISIBLE_PAGES),
   '%d in %d: %s' % (sum(inv.values()), len(inv), dict(inv)))"""

RSB_INV_NOW = """# PAID BY VC-1, 14 Oct 2026, AND THE CLAIM IS TURNED OVER.
#
# RS-1b found seventeen of these on eight pages and said so here rather
# than leaving them to be rediscovered. VC-1 took every one: three were
# correct house buttons whose class was on no list, two were
# btn-outline-light, one was a toggle painted by JavaScript, one should
# have been a primary by a decision already on the register, three became
# row actions, and the last eight - the invoice status rows - are on the
# register with a reason because they were already on house tokens.
#
# What is left is those eight, and they are NAMED now, which is a
# different thing from invisible. The number is pinned here so RS-1b's
# own finding cannot quietly grow back.
ok(sum(inv.values()) == 8 and len(inv) == 2,
   '%d button(s) in %d page(s) carry neither a listed Bootstrap colour '
   'nor a house class - VC-1 took %d of the %d RS-1b found, and named '
   'the rest' % (8, 2, N_INVISIBLE - 8, N_INVISIBLE),
   '%d in %d: %s' % (sum(inv.values()), len(inv), dict(inv)))
ok(sorted(inv) == ['customer_invoice_form.html',
                   'physical_invoice_edit.html'],
   '  and they are the two invoice status rows, on LEAVE with a reason',
   sorted(inv))"""

RSB_OL_WAS = """ok(len(outline_light) == N_OUTLINE_LIGHT,"""
RSB_OL_NOW = """# ALSO PAID. btn-outline-light is in BOOTSTRAP since VC-1 and the two
# buttons that wore it are the house row-action pair now.
ok(len(outline_light) == 0,"""

RSB_WIDEN_WAS = """ok('btn-outline-light' not in sb.BOOTSTRAP,
   '  and this round did NOT widen the vocabulary - that surfaces '
   'property-side drift in the same breath and is its own round')"""

RSB_WIDEN_NOW = """ok('btn-outline-light' in sb.BOOTSTRAP,
   '  and the vocabulary IS wider now - RS-1b declined to do it in the '
   'same breath as its own sweep, and VC-1 did it on 14 Oct')"""

RSB_CONV_WAS = """ok(len(alv_tree.CONVERTED) == CONVERTED_NOW,
   '  CONVERTED holds %d' % CONVERTED_NOW, len(alv_tree.CONVERTED))"""
RSB_CONV_NOW = """ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))"""

RSB_ROUNDS_WAS = """ok(SUFFIX in ROUNDS and ROUNDS[-1] == SUFFIX,
   '%s is the newest entry in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])"""
RSB_ROUNDS_NOW = """# A FLOOR AND AN ORDER, NOT AN EQUALITY - the repair RS-1a made to E11
# for this exact check, two rounds ago. "Newest" is true for one day.
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_pxphotos'),
   '%s is in alv_rounds.ROUNDS, after PX-1' % SUFFIX, ROUNDS[-3:])"""

# ---------------------------------------------------------------------------
# test_recipe_tones.py - RS-1a's swept-side control, and the tool again
# ---------------------------------------------------------------------------
# RS-1b pointed that comparison's two halves at the LIVE reader on purpose,
# so it would isolate the PAGES. That reasoning only holds while the TOOL
# stands still. VC-1 moved the tool, which now sees three <label> controls
# on the property side that it could not see before, so "the 117 pages are
# unchanged" came back {} versus {'unclassified': 3, 'other': 1}.
#
# Both halves go to sb_then - the tool RS-1a left - which is what isolates
# the pages once the tool is also moving. TENTH occurrence.
TONES2 = 'test_recipe_tones.py'

TONES2_WAS = """swept_now, swept_was = (buckets('other', read),
                        buckets('other', before_rs1a))"""
TONES2_NOW = """# AND BOTH HALVES WITH THE TOOL RS-1a LEFT - VC-1, 14 Oct 2026.
# RS-1b pointed these at the live reader so the check would isolate the
# PAGES, and that holds only while the tool stands still. VC-1 taught the
# scanner to see a <label>, and three of those are property-side, so the
# comparison started reporting a difference the pages do not have.
swept_now, swept_was = (buckets('other', read, sb_then),
                        buckets('other', before_rs1a, sb_then))"""

# ---------------------------------------------------------------------------
# alv_rowactions.py - a register entry needs to say WHEN it was added
# ---------------------------------------------------------------------------
# RA-5's suite reads each named page as the round that wrote the register
# left it, through as_left_by. That is right for the four entries RA-5 made
# and wrong for one VC-1 makes: the control it names did not exist in any
# snapshot older than .bak_vocab, so the suite found nothing where the
# register promised one.
#
# So an entry may say `since`, and the suite reads that page from that round
# forward. as_left_by of the newest suffix returns the LIVE file, and keeps
# returning the right thing when a later round touches the page.
RA_SINCE_WAS = """    'pantry_staples.html': {
        'count': 1,
        'classes': ('icon-delete',),"""
RA_SINCE_NOW = """    'pantry_staples.html': {
        'count': 1,
        'classes': ('icon-delete',),
        # THE ROUND THAT ADDED THIS ENTRY. test_row_exempt reads a named
        # page as the round that named it left it; without this it read
        # pantry_staples from a snapshot older than the control and found
        # nothing where the register promised one.
        'since': '.bak_vocab',"""

RE2 = 'test_row_exempt.py'

RE2_READ_WAS = """for pg, e in sorted(RA.NAMED.items()):
    src = alv_tree.code_only(now(alv_tree.path_of(pg)))"""
RE2_READ_NOW = """# AS THE ROUND THAT NAMED IT LEFT IT - VC-1, 14 Oct 2026. now() reads
# from RA-5 forward, which is right for RA-5's own four entries and wrong
# for any entry a later round adds: the control VC-1 named does not exist
# in any snapshot older than .bak_vocab, so this loop found nothing where
# the register promised one. An entry may now carry `since`.
for pg, e in sorted(RA.NAMED.items()):
    _suf = e.get('since', SUFFIX)
    _p = alv_tree.path_of(pg)
    src = alv_tree.code_only(
        as_left_by(_p, _suf, read) if as_left_by else read(_p))"""

RE2_TOTAL_WAS = """ok(total == 4, 'it names %d control(s) on %d page(s)'"""
RE2_TOTAL_NOW = """ok(total == 5, 'it names %d control(s) on %d page(s)'"""

RE2_PIN_WAS = """ok('NAMED, NOT IN A WRAPPER - 4 button(s) on 2 page(s)' in out,
   'the report names all four', out[-500:])"""
RE2_PIN_NOW = """# FIVE ON THREE SINCE VC-1, 14 Oct 2026 - pantry_staples' Remove, which
# arrived from the BUTTON census rather than this one: it was
# `btn btn-sm btn-link text-danger p-0`, and btn-link was not on
# Show-ButtonDrift's list of Bootstrap colours, so no census in this
# project could see it.
ok('NAMED, NOT IN A WRAPPER - 5 button(s) on 3 page(s)' in out,
   'the report names all five', out[-500:])"""

RW = 'test_row_wrap.py'

RW_WAS = """LOOSE_NOW = 4"""
RW_NOW = """LOOSE_NOW = 5   # VC-1, 14 Oct 2026 - a FOURTH term, and the same kind as AI-1's: pantry_staples' Remove, one control inside the chip that names the staple it removes. It reached this census from the BUTTON one, because btn-link was not on Show-ButtonDrift's colour list and nothing here could see it.   # (was 4)"""

# ---------------------------------------------------------------------------
# the registers
# ---------------------------------------------------------------------------
# NAMED, not retoned. All nine are already on house tokens - --alv-bad,
# --alv-accent, --alv-good, --alv-warn, --alv-on-accent - with a 44px
# min-height. They are not drift. Whether a status row should be five solid
# fills is a design question and it is not this round's.
LEAVE_WAS = """    'zoom-controls': 'a zoom widget',
}"""

LEAVE_NOW = """    'zoom-controls': 'a zoom widget',
    # VC-1, 14 Oct 2026 - NAMED, NOT RETONED.
    #
    # Eight buttons across customer_invoice_form and physical_invoice_edit:
    # btn-delete, btn-duplicate, btn-approve, btn-send, btn-unapprove, each
    # defined by the page itself and each already on HOUSE TOKENS -
    # --alv-bad, --alv-accent, --alv-good, --alv-warn, --alv-on-accent,
    # with a 44px min-height. Measured, not assumed. They are not drift and
    # VC-1 does not touch their colour; they were simply invisible, because
    # a page-local class is neither a Bootstrap colour nor a house one.
    #
    # WHETHER A STATUS ROW SHOULD BE FIVE SOLID FILLS is a design question
    # for its own round. This entry is what stops it being an invisible one.
    #
    # AND share-grid IS DELIBERATELY NOT HERE. It was, in the first build
    # of this round, and it was wrong: that wrapper holds FOUR buttons and
    # three of them already carry house tones - including the disabled
    # Email that RS-1b fixed the day before, `action-primary disabled-btn
    # share-btn email-btn-disabled`. A LEAVE entry short-circuits every
    # button in its wrapper, so registering it would have silenced
    # yesterday's own fix. The one undecided button there gets a house
    # class in the markup instead, which is what RS-1b did with all
    # thirteen of its own.
    #
    # THAT IS NOT A HYPOTHETICAL. Measured across all 142 pages, EIGHT
    # buttons already wearing a house tone sit inside a LEAVE wrapper and
    # are therefore never checked: three Clear Alls under .filter-header
    # and five under .input-group-append, of which THREE are
    # `action-primary btn-sm` Save buttons on property_assets. Change one
    # of those to a secondary and no gate in this project would notice.
    # test_vocabulary.py pins the number at eight so it cannot grow, and
    # LEAVE-as-a-silencer is the next thing in this line of work.
    'status-action-form': 'the invoice status row - page classes on house '
                          'tokens',
}"""

RA_NAMED_WAS = """    'create_meal_plan.html': {
        'count': 3,
        'classes': ('icon-delete',),
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal.',
    },
}"""

RA_NAMED_NOW = """    'create_meal_plan.html': {
        'count': 3,
        'classes': ('icon-delete',),
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal.',
    },
    # VC-1, 14 Oct 2026. The fifth of this shape, and it arrived from the
    # BUTTON census rather than this one: it was `btn btn-sm btn-link
    # text-danger p-0`, and btn-link was not on Show-ButtonDrift's list of
    # Bootstrap colours, so no census in this project could see it. Demetri
    # ruled it belongs here, with the four above.
    'pantry_staples.html': {
        'count': 1,
        'classes': ('icon-delete',),
        'why': 'Remove this staple - one control inside the chip that names '
               'it, beside the ingredient it removes. VC-1, and the same '
               'ruling as edit_asset.',
    },
}"""


TREE_WAS = """    # RS-1b, 14 Oct 2026 - the recipe side finishes and the drift
    # gate widens to all 142 pages. Wide from birth: it reads named
    # templates through alv_tree and builds no root of its own.
    'test_recipe_side_b.py',
]"""
TREE_NOW = """    # RS-1b, 14 Oct 2026 - the recipe side finishes and the drift
    # gate widens to all 142 pages. Wide from birth: it reads named
    # templates through alv_tree and builds no root of its own.
    'test_recipe_side_b.py',
    # VC-1, 14 Oct 2026 - the gate's VOCABULARY, after RS-1b widened
    # its page scope. Wide from birth, same shape as RS-1b's.
    'test_vocabulary.py',
]"""

ROUNDS_WAS = """    # RS-1b, 14 Oct 2026 - the 31 that were left on the recipe
    # side, and the gate goes to --recipes.
    '.bak_rsb',
]"""
ROUNDS_NOW = """    # RS-1b, 14 Oct 2026 - the 31 that were left on the recipe
    # side, and the gate goes to --recipes.
    '.bak_rsb',
    # VC-1, 14 Oct 2026 - BTN gains a tag, BOOTSTRAP two colours,
    # POSITION one house name, and _scan asks the register before
    # it gives up on a button.
    '.bak_vocab',
]"""

SUITE_WAS = """    'test_recipe_side_b.py'
)"""
SUITE_NOW = """    'test_recipe_side_b.py',
    'test_vocabulary.py'
)"""

CLAIMS_ANCHOR = """    @{ File = 'pages\\templates\\view_meal_plan.html'; Text = 'action-secondary action-danger btn-action-disabled'; What = 'a Delete reads destructive even with no permission to press it' },"""

CLAIMS = """    @{ File = 'pages\\templates\\view_meal_plan.html'; Text = 'action-secondary action-danger btn-action-disabled'; What = 'a Delete reads destructive even with no permission to press it' },
    # ------------------------------------------------- VC-1, 14 Oct 2026
    # The gate asked every PAGE after RS-1b and still not every BUTTON.
    # Three controls were a <label>, two Bootstrap colours were off the
    # list, one HOUSE name was off every list, and a decided wrapper
    # could not reach a button with no colour at all.
    @{ File = 'Show-ButtonDrift.py'; Text = '<(a|button|span|label)'; What = 'the button scanner can see a <label>, which three file pickers are' },
    @{ File = 'Show-ButtonDrift.py'; Text = 'btn-outline-light'; What = 'and six of Bootstrap''s eight outline colours is not the list' },
    @{ File = 'Show-ButtonDrift.py'; Text = 'def print_painted'; What = 'and a button painted by page CSS or JavaScript is counted, not dropped' },
    @{ File = 'pages\\templates\\my_profile.html'; Text = 'btn action-secondary btn-sm'; What = 'Upload Photo stops being Bootstrap blue at 3.98 to 1' },
    @{ File = 'pages\\templates\\ingredient_families.html'; Text = 'icon-action-btn icon-delete'; What = 'and the family icons stop being a near-white glyph on green at 2.97 to 1' },
    @{ File = 'pages\\templates\\create_meal_plan.html'; Text = 'aria-pressed'; What = 'the Favourites toggle carries its state in aria-pressed, not an inline style'; },
    @{ File = 'pages\\templates\\create_meal_plan.html'; Text = 'btn.style.background'; What = 'and no JavaScript paints it any more'; Absent = $true; Code = $true },"""


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
    raise SystemExit('VC-1 REFUSED: %s' % msg)


def fit(text, lit):
    """A multi-line anchor written LF here, converted to whatever THIS file
    mostly uses. PX-1's hazard, and it bites again: the seven templates
    VC-1 edits are three LF, three CRLF and one mixed. Normalising a file
    to get a match turns a one-line change into a four-thousand-line diff
    nobody can review. Single-line anchors are left exactly alone."""
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
    w = fit(text, was)
    once(text, was, where)
    return text.replace(w, fit(text, now), 1)


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
    # ALREADY APPLIED COMES FIRST, and it is asked of the TOOL: if the
    # scanner can already see a <label>, this round has run.
    drift = read(os.path.join(root, DRIFT))
    if '<(a|button|span|label)' in drift:
        print('VC-1  already applied - the scanner already reads a '
              '<label> and btn-outline-light.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # Show-ButtonDrift.py - the vocabulary and the structural hole
    p = os.path.join(root, DRIFT)
    s = drift
    s = swap(s, BTN_WAS, BTN_NOW, '%s (BTN gains a tag)' % DRIFT)
    s = swap(s, BOOT_WAS, BOOT_NOW, '%s (BOOTSTRAP)' % DRIFT)
    s = swap(s, POS_WAS, POS_NOW, '%s (POSITION)' % DRIFT)
    s = swap(s, SKIP_WAS, SKIP_NOW, '%s (skip_reason)' % DRIFT)
    s = swap(s, LEAVE_WAS, LEAVE_NOW, '%s (LEAVE)' % DRIFT)
    s = swap(s, SCAN_WAS, SCAN_NOW, '%s (_scan asks the register first)' % DRIFT)
    s = swap(s, PRINT_PAINTED_ANCHOR, PRINT_PAINTED,
             '%s (the painted report)' % DRIFT)
    s = swap(s, MAIN_LOOP_WAS, MAIN_LOOP_NOW, '%s (main collects it)' % DRIFT)
    s = swap(s, MAIN_COUNT_WAS, MAIN_COUNT_NOW, '%s (main counts it)' % DRIFT)
    s = swap(s, MAIN_CLEAN_WAS, MAIN_CLEAN_NOW,
             '%s (the clean branch prints it)' % DRIFT)
    s = swap(s, MAIN_UNCL_WAS, MAIN_UNCL_NOW,
             '%s (the drift branch prints it)' % DRIFT)
    out[p] = s

    # ---------------------------------------------------------------- 2
    # four tones
    for page, was_, now_, what in TONES:
        q = alv_tree.path_of(page)
        t = out.get(q, read(q))
        out[q] = swap(t, was_, now_, '%s (%s)' % (page, what))

    # ---------------------------------------------------------------- 3
    # three controls that become row actions
    q = alv_tree.path_of('ingredient_families.html')
    t = read(q)
    t = swap(t, FAM_WRAP_WAS, FAM_WRAP_NOW,
             'ingredient_families.html (the wrapper, layout-identical)')
    t = swap(t, FAM_EDIT_WAS, FAM_EDIT_NOW,
             'ingredient_families.html (the edit pencil)')
    t = swap(t, FAM_DEL_WAS, FAM_DEL_NOW,
             'ingredient_families.html (the trash)')
    out[q] = t

    q = alv_tree.path_of('pantry_staples.html')
    out[q] = swap(read(q), PANTRY_WAS, PANTRY_NOW,
                  'pantry_staples.html (Remove this staple)')

    # ---------------------------------------------------------------- 4
    # the toggle that was painted by JavaScript
    q = alv_tree.path_of('create_meal_plan.html')
    t = read(q)
    t = swap(t, FAV_WAS, FAV_NOW, 'create_meal_plan.html (the toggle)')
    t = swap(t, FAV_JS_WAS, FAV_JS_NOW,
             'create_meal_plan.html (its handler)')
    t = swap(t, FAV_RESET_WAS, FAV_RESET_NOW,
             'create_meal_plan.html (the reset on open)')
    t = swap(t, FAV_CLEAR_WAS, FAV_CLEAR_NOW,
             'create_meal_plan.html (and the reset in clearRecipeFilters)')
    out[q] = t

    # --------------------------------------------------------------- 4b
    # D-1's height census, which VC-1 made able to see three controls
    p = os.path.join(root, BH)
    s = read(p)
    if 'property_assets.html' in s.split('STRAYS = {')[1].split('}')[0]:
        refuse('%s already names the property_assets stray' % BH)
    s = swap(s, BH_PINS_WAS, BH_PINS_NOW, '%s (the modal pin)' % BH)
    s = swap(s, BH_LOOSE_WAS, BH_LOOSE_NOW, '%s (the loose pins)' % BH)
    s = swap(s, BH_STRAYS_WAS, BH_STRAYS_NOW, '%s (STRAYS)' % BH)
    out[p] = s

    # --------------------------------------------------------------- 4c
    # E11's suite, and one suite whose colour census came DOWN
    p = os.path.join(root, JS)
    s = read(p)
    if 'btn_of(left(DRIFT))' in s:
        refuse('%s already reads the tool as E11 left it' % JS)
    s = swap(s, JS_TIGHT_WAS, JS_TIGHT_NOW, '%s (section 3)' % JS)
    s = swap(s, JS_PRICE_WAS, JS_PRICE_NOW, '%s (the price, both ways)' % JS)
    s = swap(s, JS_ROWS_WAS, JS_ROWS_NOW, '%s (the per-row diff)' % JS)
    out[p] = s

    p = os.path.join(root, CSS)
    s = read(p)
    s = swap(s, CSS_SCRIPT_WAS, CSS_SCRIPT_NOW, '%s (the script count)' % CSS)
    s = swap(s, CSS_CTX_WAS, CSS_CTX_NOW, '%s (the context split)' % CSS)
    s = swap(s, CSS_SAFE_WAS, CSS_SAFE_NOW, '%s (the var-safe subset)' % CSS)
    out[p] = s

    p = os.path.join(root, NEU)
    out[p] = swap(read(p), NEU_WAS, NEU_NOW, '%s (the cross-check)' % NEU)

    # --------------------------------------------------------------- 4d
    # RS-1b's suite: its debt, turned over. And RS-1a's swept control.
    p = os.path.join(root, RSB)
    s = read(p)
    if 'PAID BY VC-1' in s:
        refuse('%s already turned over' % RSB)
    s = swap(s, RSB_INV_WAS, RSB_INV_NOW, '%s (the 17)' % RSB)
    s = swap(s, RSB_OL_WAS, RSB_OL_NOW, '%s (btn-outline-light)' % RSB)
    s = swap(s, RSB_WIDEN_WAS, RSB_WIDEN_NOW, '%s (the vocabulary)' % RSB)
    s = swap(s, RSB_CONV_WAS, RSB_CONV_NOW, '%s (CONVERTED)' % RSB)
    s = swap(s, RSB_ROUNDS_WAS, RSB_ROUNDS_NOW, '%s (ROUNDS)' % RSB)
    out[p] = s

    p = os.path.join(root, TONES2)
    out[p] = swap(read(p), TONES2_WAS, TONES2_NOW,
                  '%s (the swept-side control)' % TONES2)

    # --------------------------------------------------------------- 4e
    # the row-action register learns WHEN an entry was added
    p = os.path.join(root, RE2)
    s = read(p)
    s = swap(s, RE2_READ_WAS, RE2_READ_NOW, '%s (the reader)' % RE2)
    s = swap(s, RE2_TOTAL_WAS, RE2_TOTAL_NOW, '%s (the total)' % RE2)
    s = swap(s, RE2_PIN_WAS, RE2_PIN_NOW, '%s (the report pin)' % RE2)
    out[p] = s

    p = os.path.join(root, RW)
    out[p] = swap(read(p), RW_WAS, RW_NOW, '%s (the loose count)' % RW)

    # ---------------------------------------------------------------- 5
    # the row-action register
    p = os.path.join(root, RA)
    s = swap(read(p), RA_NAMED_WAS, RA_NAMED_NOW, '%s (NAMED)' % RA)
    s = swap(s, RA_SINCE_WAS, RA_SINCE_NOW, '%s (the since marker)' % RA)
    out[p] = s

    # ---------------------------------------------------------------- 6
    # the gate, the registers and the two counters kept by hand
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_vocabulary.py' in s:
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
                  'VC-1, 14 Oct 2026 - this round own suite. The gate '
                  'vocabulary, after RS-1b widened its page scope.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'VC-1, 14 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('VC-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('VC-1 applied.')
    print('   BTN gains <label>; BOOTSTRAP gains btn-outline-light, '
          'btn-outline-dark, btn-link')
    print('   POSITION gains action-field-add, with its own skip_reason')
    print('   _scan asks the register before dropping an uncoloured button')
    print('   %d tone(s), %d control(s) onto the row-action component, '
          '1 toggle onto aria-pressed'
          % (N_TONED, N_ROW_ACTIONS))
    print('   %d button(s) named on the register rather than retoned'
          % N_REGISTER)
    print('   painted-elsewhere %d -> %d' % (N_PAINTED_WAS, N_PAINTED_NOW))
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
