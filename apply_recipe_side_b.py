# -*- coding: utf-8 -*-
"""apply_recipe_side_b.py - round RS-1b, 14 Oct 2026.

THE REST OF THE RECIPE SIDE, AND THE GATE WIDENS TO EVERY PAGE.

RS-1a took the 35 buttons that carried a Bootstrap colour somebody had
already decided. This is everything left: 18 disagreements the instrument
reported, 13 controls nobody had ever looked at, one wrong entry on the
role register, and then the one line that is the round's real product -

    Show-ButtonDrift.py --strict          117 of 142 pages
    Show-ButtonDrift.py --strict --recipes          142

The push gate's own comment has said "it walks every template" since
August. It did not. It asked the property module, because the recipe and
meal-plan side was deferred by name, and the sentence stayed in the file.

THREE PROPOSALS OF MINE THAT MEASUREMENT KILLED
------------------------------------------------
1. A NAVIGATION RULE, which Demetri approved on my say-so: "a bar whose
   only non-Back item is a link to another page is navigation, not the
   page's verb". Tested afterwards against all 142 pages it matches
   ELEVEN bars and six are correct primaries - Add Country, Add
   Reporting FI, Start Submission, Add Workspace, Go to Login, and
   friday_status_report's SUBMIT FSR, which is a fault Demetri reported
   and this programme fixed. WITHDRAWN. See NOT_THE_VERB in
   Show-ButtonDrift.py for what replaced it.

2. "A LABEL BUILT FROM A TEMPLATE CONDITIONAL IS A CHOOSER", to catch
   celebration_calendar's view toggle in is_chooser(). Ten bar buttons
   have a conditional label and NINE are real Save buttons. It would
   have demoted every Save in the application.

3. THE SIX LEAVES. My survey proposed leaving six of the thirteen alone,
   five of them as "welded to an input; Bootstrap owns the geometry".
   Measured one at a time, not one survives:

     - .servings-input-group is the PAGE'S OWN flex container with
       `gap: 15px`. Nothing is welded to anything; there are fifteen
       pixels of air either side of the input.
     - create_meal_plan's search button IS welded, in a bare
       .input-group - and login.html and password_set.html both put a
       welded icon button on `btn action-secondary` already, with the
       reason written in a comment above it: "Bootstrap keeps the
       geometry, so only the colour moves".
     - recipe_management's Clear All is the EIGHTEENTH instance of one
       control. Thirteen of the other seventeen are still Bootstrap
       outline-grey behind LEAVE['filter-header'] - but THREE are
       already `btn action-secondary btn-sm`, shipped and live on
       cash_receipts, celebration_management and customer_list. A fourth
       joining them follows a decision; it does not make one.
     - import_recipe's Remove reads destructive by TONE now, which is
       the bargain base.html already strikes everywhere else: outlined
       at rest, red only on hover.

   So RS-1b adds NOTHING to LEAVE and nothing to DECIDED. All thirteen
   decisions are written into the markup, where the classifier picks
   them up through the house-class branch it already has, and where a
   person reading the page can see them.

AND ONE MORE, WHICH MAKES THIS ROUND BIGGER BY ONE
---------------------------------------------------
My survey listed wcim_recipe_quick_view's OPEN FULL RECIPE as a
promotion to suppress. It is not. Of the 54 modal-footer primaries in
this application exactly two are a link to another page: that one, and
properties_edit's GO TO EXPENSES - which ships as a solid
`btn action-primary` and which plan_footer's own note names as one of
the five v1 got wrong. Same shape, same decision already taken. So four
promotions are right and three are wrong, not three and four.

WHAT THE GATE STILL CANNOT SEE, SAID HERE AND NOT DISCOVERED LATER
-------------------------------------------------------------------
Widening the PAGE scope does not widen the VOCABULARY. Seventeen buttons
across eight pages carry neither a Bootstrap colour this tool lists nor a
house class, so every census in this project passes straight over them:

    customer_invoice_form 5   physical_invoice_edit 3   property_assets 3
    ingredient_families 2     create_meal_plan 1       pantry_staples 1
    meal_plan_shopping_list 1 error_pages/connectivity_error 1

Two of them are `btn-outline-light`, which IS a Bootstrap colour and
which BOOTSTRAP does not list - the exact blind spot the comment beside
the outline variants warns about, one shade further on. The rest are
inline style, btn-link, or a page's own class; create_meal_plan's
Favourites toggle is painted by JavaScript writing btn.style.background
directly, which is the control B-1 already fixed once on
recipe_management.

NOT FIXED HERE, deliberately: widening BOOTSTRAP surfaces drift on the
PROPERTY side in the same breath, and a round does not get to widen a
census and sweep what it finds in one unreviewed step. It is the next
thing in this line of work.

See test_recipe_side_b.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_rsb'
SUITE = 'test_recipe_side_b.py'
DRIFT = 'Show-ButtonDrift.py'
SWEEP = 'test_button_sweep.py'
TONES = 'test_recipe_tones.py'
RETONE = 'test_retone.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13

# The register counters these rounds keep by hand.
CONVERTED_WAS, CONVERTED_NOW = 74, 75
ALIAS_WAS, ALIAS_NOW = 59, 61
ALIAS_P_WAS, ALIAS_P_NOW = 29, 30
ALIAS_S_WAS, ALIAS_S_NOW = 30, 31

# What the gate asked before and after. Not typed from memory: the suite
# re-derives both from alv_tree and fails if either moves.
GATE_WAS, GATE_NOW = 117, 142

EDITS = [
    ('celebration_calendar.html',
     '<a href="?month={{ next_month }}&year={{ next_year }}" class="btn btn-outline-primary">',
     '<a href="?month={{ next_month }}&year={{ next_year }}" class="btn action-secondary">',
     'calendar Next'),
    ('celebration_calendar.html',
     '<a href="?month={{ prev_month }}&year={{ prev_year }}" class="btn btn-outline-primary">',
     '<a href="?month={{ prev_month }}&year={{ prev_year }}" class="btn action-secondary">',
     'calendar Previous'),
    ('create_meal_plan.html',
     '<button class="btn btn-outline-danger w-100" onclick="clearRecipeFilters()">',
     '<button class="btn action-secondary w-100" onclick="clearRecipeFilters()">',
     'Clear Filters, the 18th of its kind'),
    ('create_meal_plan.html',
     '<button class="btn btn-primary" onclick="searchRecipesInSelector()">',
     '<button class="btn action-secondary" onclick="searchRecipesInSelector()">',
     'the search button welded to its field'),
    ('import_recipe.html',
     '<button type="submit" class="btn btn-info btn-lg" id="processBtn" disabled>',
     '<button type="submit" class="btn action-primary btn-lg" id="processBtn" disabled>',
     'Extract Recipe with AI, the page itself'),
    ('import_recipe.html',
     '<button type="button" class="btn btn-sm btn-danger" onclick="clearFile()">',
     '<button type="button" class="btn action-secondary action-danger btn-sm" onclick="clearFile()">',
     'Remove, beside the file it removes'),
    ('recipe_management.html',
     '<button type="button" class="btn btn-outline-secondary btn-sm" onclick="clearAllRecipeFilters(event)">',
     '<button type="button" class="btn action-secondary btn-sm" onclick="clearAllRecipeFilters(event)">',
     'Clear All, the 18th of its kind'),
    ('view_recipe.html',
     '<button class="btn btn-info" onclick="copyToClipboard()">',
     '<button class="btn action-secondary" onclick="copyToClipboard()">',
     'Copy, beside three house siblings'),
    ('view_recipe.html',
     '<button class="btn btn-secondary" onclick="printShoppingList()">',
     '<button class="btn action-secondary" onclick="printShoppingList()">',
     'Print, beside three house siblings'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-outline-primary" onclick="aiRetry()">',
     '<button type="button" class="btn action-primary" onclick="aiRetry()">',
     'Try again, the way out of an AI error'),
    ('view_recipe.html',
     '<button class="btn btn-outline-secondary" onclick="adjustServings(-1)">',
     '<button class="btn action-secondary" onclick="adjustServings(-1)">',
     'the servings stepper, minus'),
    ('view_recipe.html',
     '<button class="btn btn-outline-secondary" onclick="adjustServings(1)">',
     '<button class="btn action-secondary" onclick="adjustServings(1)">',
     'the servings stepper, plus'),
    ('wcim_landing.html',
     '<button type="submit" name="action" value="skip" class="btn btn-outline-secondary">',
     '<button type="submit" name="action" value="skip" class="btn action-secondary">',
     'Skip extras, beside Continue'),
    ('celebration_management.html',
     '<button class="btn action-primary btn-action-disabled" disabled title="No permission to edit">',
     '<button class="btn action-primary disabled-btn btn-action-disabled" disabled title="No permission to edit">',
     'Add Contact - add disabled-btn'),
    ('celebration_management.html',
     '<button class="btn action-secondary btn-action-disabled" disabled title="No permission to edit">',
     '<button class="btn action-secondary disabled-btn btn-action-disabled" disabled title="No permission to edit">',
     'Import from Excel - add disabled-btn'),
    ('meal_plan_shopping_list.html',
     '<button disabled class="btn action-primary share-btn email-btn-disabled" title="No permission to send email">',
     '<button disabled class="btn action-primary disabled-btn share-btn email-btn-disabled" title="No permission to send email">',
     'Email - add disabled-btn'),
    ('measurement_units_management.html',
     '<button type="button" class="btn action-primary" disabled style="opacity: 0.6; cursor: not-allowed;" title="No permission to edit">',
     '<button type="button" class="btn action-primary disabled-btn" disabled style="opacity: 0.6; cursor: not-allowed;" title="No permission to edit">',
     'Add Measurement Unit - add disabled-btn'),
    ('preview_imported_recipe.html',
     '<button type="button" class="btn action-secondary" onclick="confirmAddIngredient()">',
     '<button type="button" class="btn action-primary" onclick="confirmAddIngredient()">',
     'Add Ingredient - the lone verb of its footer'),
    ('preview_imported_recipe.html',
     '<button type="button" class="btn action-secondary" onclick="confirmAddMeasurement()">',
     '<button type="button" class="btn action-primary" onclick="confirmAddMeasurement()">',
     'Add Measurement - the lone verb of its footer'),
    ('preview_imported_recipe.html',
     '<button type="button" class="btn btn-sm action-secondary action-danger" onclick="confirmDeleteRecipeDocument({{ recipe.recipe_id }})">',
     '<button type="button" class="btn action-secondary action-danger btn-sm" onclick="confirmDeleteRecipeDocument({{ recipe.recipe_id }})">',
     'Delete Current Document - canonical class order'),
    ('preview_imported_recipe.html',
     '<a id="recipeDocDownloadLink" href="#" class="btn action-secondary" target="_blank">',
     '<a id="recipeDocDownloadLink" href="#" class="btn action-primary" target="_blank">',
     'Download - the lone verb of its footer'),
    ('preview_imported_recipe.html',
     '<button type="button" class="btn btn-sm action-secondary ml-3" onclick="viewRecipeDocument(\'{{ recipe.recipe_document.url|escapejs }}\', \'{{ recipe.recipe_document.name|escapejs }}\')">',
     '<button type="button" class="btn action-secondary btn-sm ml-3" onclick="viewRecipeDocument(\'{{ recipe.recipe_document.url|escapejs }}\', \'{{ recipe.recipe_document.name|escapejs }}\')">',
     'View - canonical class order'),
    ('recipe_management.html',
     '<span class="btn action-primary dropdown-btn" style="opacity:0.6; cursor:not-allowed; pointer-events:none;">',
     '<span class="btn action-primary disabled-btn dropdown-btn" style="opacity:0.6; cursor:not-allowed; pointer-events:none;">',
     'Add Recipe - add disabled-btn'),
    ('unit_conversions_management.html',
     '<button class="btn action-primary" disabled style="opacity: 0.6; cursor: not-allowed;" title="No permission to edit">',
     '<button class="btn action-primary disabled-btn" disabled style="opacity: 0.6; cursor: not-allowed;" title="No permission to edit">',
     'Add New Conversion - add disabled-btn'),
    ('unit_conversions_management.html',
     '<button class="btn action-secondary" disabled style="opacity: 0.6; cursor: not-allowed;" title="No permission to edit">',
     '<button class="btn action-secondary disabled-btn" disabled style="opacity: 0.6; cursor: not-allowed;" title="No permission to edit">',
     'Missing Conversions () - add disabled-btn'),
    ('view_meal_plan.html',
     '<button type="button"\n                    class="btn action-secondary"\n                    data-delete-url="{% url \'delete_meal_plan\' meal_plan.meal_plan_id %}"\n                    onclick="confirmDelete(this, \'{{ meal_plan.plan_name|escapejs }}\')">',
     '<button type="button"\n                    class="btn action-secondary action-danger"\n                    data-delete-url="{% url \'delete_meal_plan\' meal_plan.meal_plan_id %}"\n                    onclick="confirmDelete(this, \'{{ meal_plan.plan_name|escapejs }}\')">',
     'Delete - a Delete reads destructive'),
    ('view_meal_plan.html',
     '<span class="btn btn-action-disabled action-secondary" title="No permission to delete">',
     '<span class="btn action-secondary action-danger btn-action-disabled" title="No permission to delete">',
     'Delete - a Delete reads destructive'),
    ('view_meal_plan.html',
     '<span class="btn btn-action-disabled action-secondary" title="No permission to duplicate">',
     '<span class="btn action-secondary btn-action-disabled" title="No permission to duplicate">',
     'Duplicate - canonical class order'),
    ('view_meal_plan.html',
     '<span class="btn btn-action-disabled action-secondary" title="No permission to edit">',
     '<span class="btn action-secondary btn-action-disabled" title="No permission to edit">',
     'Edit - canonical class order'),
    ('view_recipe.html',
     '<button class="btn action-secondary share-btn-disabled" disabled title="No permission to send email">',
     '<button class="btn action-secondary disabled-btn share-btn-disabled" disabled title="No permission to send email">',
     'Email - add disabled-btn'),
    ('wcim_recipe_quick_view.html',
     '<a href="{% url \'view_recipe\' recipe.recipe_id %}" class="btn action-secondary">',
     '<a href="{% url \'view_recipe\' recipe.recipe_id %}" class="btn action-primary">',
     'Open full recipe - the lone verb of its footer'),
]


# ---------------------------------------------------------------------------
# Show-ButtonDrift.py - the register entry that came off, and the map
# ---------------------------------------------------------------------------
DFLEX_WAS = """    'header-actions':          [('*', S)],
    'd-flex':                  [('*', S)],
"""

DFLEX_NOW = '''    'header-actions':          [('*', S)],
    # 'd-flex' WAS HERE. It came off in RS-1b, 14 Oct 2026.
    #
    # It is a Bootstrap LAYOUT utility sitting on a register of ROLES.
    # Measured across all 142 pages it contains six buttons; two of
    # those are invisible to this scan for other reasons, and of the
    # four it actually spoke for, FOUR are recipe-side and ZERO are on
    # the property side. Its only live effect was demoting
    # pantry_staples' Add Staple, because everything under a d-flex was
    # declared a secondary by a map that cannot tell a card from a
    # header row.
    #
    # All four reach their tone the ordinary way now: each carries a
    # house class, so plan_bar() re-derives it, and plan_bar is a fixed
    # point on its own output. Drift 22 -> 21 on this line alone and
    # nothing else in the application moved.
    #
    # STILL ON THIS REGISTER AND STILL LAYOUT NAMES: text-center (6
    # buttons), alert (8), col-md-6 (1), detail-row (1), col-12 (0).
    # None is misbehaving today. col-md-3 nearly joined them in this
    # round and did not - which is why no wrapper was named for
    # create_meal_plan's filter row and the decision went into the
    # markup instead.
'''

NTV_ANCHOR = """# Modal-footer vocabulary."""

NTV = '''# ---------------------------------------------------------------------------
# Bar buttons that are NOT the page's verb - named ONE AT A TIME
# ---------------------------------------------------------------------------
# page -> [(label fragment, the reason)]. Consulted only by the lone-verb
# rule in plan_bar(), and only ever to STOP a promotion: nothing here can
# give a button a tone, so a wrong entry costs a missing primary and can
# never cause a wrong one.
#
# WHY A MAP AND NOT A RULE. RS-1b proposed one - "a bar whose only non-Back
# item is a link to another page is navigation, not the page's verb" - and
# Demetri approved it on my say-so. Tested afterwards against all 142 pages
# it matches ELEVEN bars, and six of those are correct primaries: Add
# Country, Add Reporting FI, Start Submission, Add Workspace, Go to Login,
# and friday_status_report's SUBMIT FSR, which is a fault Demetri reported
# and this programme fixed. The rule was withdrawn.
#
# The second candidate was "a label built from a template conditional is a
# chooser", for celebration_calendar's view toggle - which carries no marker
# of any kind: `btn action-secondary`, id="viewToggleBtn",
# onclick="toggleCalendarView()", and a human comment above it. Ten bar
# buttons have a conditional label and NINE are real Save buttons. It would
# have demoted every Save in the application, and plan_bar's own note below
# already names customer_form.html as this exact shape AND as the page's
# verb.
#
# So: an explicit map with a reason each. The precedent is
# backfill_passport_holder's ALIASES, where an explicit map was chosen over
# a first-word rule that "stops looking safe the day a household holds a
# Demetri and a Demetris".
#
# THE PRINCIPLED FIX EXISTS and is a larger decision: a house marker class
# for a view toggle, the way .alv-seg marks a segment. That touches
# base.html, so it is left for its own round - and when it lands, the
# celebration_calendar entry here comes out.
NOT_THE_VERB = {
    'pantry_staples.html': [
        ('families', 'a link to the Families list - another page, not '
                     'this one\\'s verb')],
    'wcim_results.html': [
        ('start over', 'returns to the start of the search')],
    'celebration_calendar.html': [
        ('calendar view', 'the Calendar/Timeline toggle - it asks which '
                          'view you are looking at')],
}


def not_the_verb(page, label):
    """The recorded reason this bar button is not the page's verb, or None.

    ASKED OF THE TOOL rather than re-implemented. The lone-verb rule has
    two copies - here and in test_button_sweep.py section 9 - and the
    last time one of them learned something the other did not, the other
    reported finance_pl_act's YEAR DROPDOWN as a missing primary. [PM-1]
    """
    low = (label or '').lower()
    for frag, why in NOT_THE_VERB.get(page or '', ()):
        if frag in low:
            return why
    return None


# Modal-footer vocabulary.'''

PLAN_WAS = """def plan_bar(items, in_bar=False):"""
PLAN_NOW = """def plan_bar(items, in_bar=False, page=None):"""

REAL_WAS = """            and not is_chooser(lab, cls)]"""
REAL_NOW = """            and not is_chooser(lab, cls)
            # AND A NAMED EXCEPTION IS NEVER THE VERB - RS-1b, 14 Oct
            # 2026. Three recipe-side bars hold exactly one real button
            # and it is navigation or a view toggle. See NOT_THE_VERB
            # above for why that is a map and not a rule, and for the
            # rule I proposed that would have demoted Submit FSR.
            and not not_the_verb(page, lab)]"""

SCAN1_WAS = """        tones = (plan_footer(items) if kind == 'modal footer'
                 else plan_bar(items, in_bar=True))"""
SCAN1_NOW = """        tones = (plan_footer(items) if kind == 'modal footer'
                 else plan_bar(items, in_bar=True, page=name))"""

SCAN2_WAS = """            tone = plan_bar([(lab, cls, open_tag)])[0]"""
SCAN2_NOW = """            tone = plan_bar([(lab, cls, open_tag)], page=name)[0]"""

# ---------------------------------------------------------------------------
# test_button_sweep.py - the OTHER copy of the lone-verb rule
# ---------------------------------------------------------------------------
LONE_WAS = """                and not sb.is_chooser(sb.label_of(b.group(3)),
                                      b.group(2))]"""
LONE_NOW = """                and not sb.is_chooser(sb.label_of(b.group(3)),
                                      b.group(2))
                # RS-1b, 14 Oct 2026 - AND THE SAME FOR A NAMED
                # EXCEPTION, for exactly the reason PM-1 gives three
                # lines up. FILES is the 117-page sweep scope, so none
                # of the three pages in sb.NOT_THE_VERB is in this
                # corpus TODAY and this clause changes no result. It is
                # here because the rule has two copies and they have to
                # learn together - the alternative is finding out on the
                # day the corpus widens.
                and not sb.not_the_verb(f, sb.label_of(b.group(3)))]"""

# ---------------------------------------------------------------------------
# test_recipe_tones.py - RS-1a's suite, repaired. THE SEVENTH OCCURRENCE.
# ---------------------------------------------------------------------------
# RS-1a's section 2 counts the six buckets it handed to RS-1b by reading the
# recipe side LIVE. That is a SNAPSHOT claim - "this is what RS-1a left" -
# and a live read of a snapshot stops being true the moment the next round
# runs. Seven occurrences now: E15's counters, F2b's render, E11's four
# checks, RS-1a's own repair of both of those, and these.
#
# WHICH HALF STAYS LIVE MATTERS, AND IT IS NOT THE SAME EVERYWHERE. RS-1a's
# `now['bootstrap'] == 0` is an INVARIANT - no Bootstrap colour is left on
# the recipe side - and it is read live on purpose, because the whole claim
# is that it is still true today. It is left exactly as it stands.
TONES_READER_ANCHOR = '''def left(name):
    p = os.path.join(ROOT, name)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)
'''

TONES_READER = '''def left(name):
    p = os.path.join(ROOT, name)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


# ADDED BY RS-1b, 14 Oct 2026 - THE RECIPE SIDE AS RS-1a LEFT IT.
#
# Section 2 below counts what RS-1a handed over. That is a snapshot and has
# to be read as one: RS-1b took all 22 disagreements and all 13 undecided
# controls, so a LIVE read of those counters returns zero and RS-1a's own
# suite reports that RS-1a did nothing.
def as_rs1a_left_it(p):
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


def before_rs1a(p):
    # And the state BEFORE RS-1a: its own backup where it made one, else
    # the page as it left it - which, for a page RS-1a never touched, is
    # the same thing. was() could not say that. It fell back to the LIVE
    # file, so two of the thirty-five came back as thirty-three the
    # moment RS-1b edited those two pages.
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else as_rs1a_left_it(p)
'''

TONES_B2_WAS = '''now = buckets('recipe', read)
ok(now['bootstrap'] == 0,
   'not one Bootstrap-toned button is left on the recipe side',
   now['bootstrap'])

# THE FORWARD HALF, read from the backups: it was 35, so the zero above
# is a round that happened and not a scanner that went quiet.
before = buckets('recipe', was)
ok(before['bootstrap'] == N_ELEMENTS,
   '  and there were %d before, read from the backups' % N_ELEMENTS,
   before['bootstrap'])

for k, n in sorted(LEFT.items()):
    ok(now[k] == n,
       '%-12s still %2d - RS-1b owns it and RS-1a did not touch it'
       % (k, n), '%d' % now[k])
ok(now['other'] == 0, 'and nothing fell into a bucket nobody named',
   now['other'])
ok(sum(now[k] for k in LEFT if k != 'unclassified') == 22,
   'the recipe side is down to 22 disagreement(s) from 57',
   sum(now[k] for k in LEFT if k != 'unclassified'))
'''

TONES_B2_NOW = '''now = buckets('recipe', read)
ok(now['bootstrap'] == 0,
   'not one Bootstrap-toned button is left on the recipe side',
   now['bootstrap'])

# AS RS-1a LEFT IT - REPAIRED BY RS-1b, 14 Oct 2026. Every count below is a
# statement about the handover, so every one of them reads the snapshot.
# The invariant above stays live. See as_rs1a_left_it near the top.
asleft = buckets('recipe', as_rs1a_left_it, sb_then)

# THE FORWARD HALF, read from the backups: it was 35, so the zero above
# is a round that happened and not a scanner that went quiet.
before = buckets('recipe', before_rs1a, sb_then)
ok(before['bootstrap'] == N_ELEMENTS,
   '  and there were %d before, read from the backups' % N_ELEMENTS,
   before['bootstrap'])

for k, n in sorted(LEFT.items()):
    ok(asleft[k] == n,
       '%-12s was %2d when RS-1a finished - RS-1b owns it'
       % (k, n), '%d' % asleft[k])
ok(asleft['other'] == 0, 'and nothing fell into a bucket nobody named',
   asleft['other'])
ok(sum(asleft[k] for k in LEFT if k != 'unclassified') == 22,
   'the recipe side came down to 22 disagreement(s) from 57',
   sum(asleft[k] for k in LEFT if k != 'unclassified'))
# AND THE HALF ONLY RS-1b CAN SAY: all 22 and all 13 are gone now, which is
# the thing that let the push gate widen. Read LIVE, because that is what
# has to be true today.
ok(sum(now[k] for k in LEFT) == 0,
   '  and RS-1b took every one of them - 22 + 13 -> 0, live',
   '%s' % {k: now[k] for k in LEFT if now[k]})
'''

TONES_SWEPT_WAS = """swept_now, swept_was = buckets('other', read), buckets('other', was)"""
TONES_SWEPT_NOW = """swept_now, swept_was = (buckets('other', read),
                        buckets('other', before_rs1a))
# AND BOTH TOOLS AGREE ABOUT THE PROPERTY SIDE - RS-1b, 14 Oct 2026.
# The two reads above use the LIVE reader on purpose, so that check
# isolates the PAGES. This one isolates the TOOL: d-flex reached four
# buttons and all four are recipe-side, and NOT_THE_VERB names three
# recipe pages, so RS-1b's changes to the scanner must be invisible
# over the 117.
ok(buckets('other', read) == buckets('other', read, sb_then),
   '  and the scanner RS-1b changed reads them identically to the '
   'one RS-1a left')"""

TONES_GATE_WAS = '''# THE GATE IS STILL NARROW, ON PURPOSE, AND SAYS SO HERE RATHER THAN
# BEING DISCOVERED AGAIN. RS-1b widens it.
ps1 = read(os.path.join(ROOT, PS1))
ok('--strict' in ps1 and '--strict --recipes' not in ps1,
   'the push gate still runs --strict WITHOUT --recipes - 117 of 142 '
   'pages, and RS-1b is what widens it')'''

TONES_GATE_NOW = '''# THE GATE WAS NARROW ON PURPOSE AND RS-1b WIDENED IT. RS-1a wrote this
# check the other way round - as the thing RS-1b owed it - and RS-1b turned
# it over rather than deleting it. A claim allowed to disappear on the day
# it comes true leaves no record that it was ever owed.
ps1 = read(os.path.join(ROOT, PS1))
ok('--strict --recipes' in ps1,
   'the push gate runs --strict --recipes now - all 142 pages, which is '
   'what RS-1a said RS-1b owed it')'''

# AND THE INSTRUMENT OF ITS TIME - the eighth occurrence, and the first that
# is about the TOOL rather than the pages.
#
# Reading RS-1a's pages with RS-1b's reader is still a live read of a
# snapshot; it just hides better. RS-1b took d-flex off DECIDED and put
# three bar buttons on NOT_THE_VERB, so the same handover re-buckets under
# it: 35 Bootstrap-toned becomes 33 plus 2 unclassified (ingredient_families'
# and pantry_staples' Reset, both btn-outline-danger under a d-flex, drift
# only because d-flex was on the register), 7 promotions become 4 and the 1
# demotion becomes 0. RS-1a did not do less. The question changed under it.
#
# So section 2 asks Show-ButtonDrift.py AS RS-1a LEFT IT, and everything
# from section 3 on goes on asking the live one.
TOOL_ANCHOR = """_spec = importlib.util.spec_from_file_location('_sb_rs1a',
                                               os.path.join(ROOT, DRIFT))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)
"""

TOOL_NOW = '''_spec = importlib.util.spec_from_file_location('_sb_rs1a',
                                               os.path.join(ROOT, DRIFT))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)


# ADDED BY RS-1b, 14 Oct 2026 - THE TOOL AS RS-1a LEFT IT, loaded beside
# the live one. Written into this process's own SCRATCH directory, which
# mkdtemp named for this process alone, and handed back the repo's ROOT and
# TPL because a module that works out where the templates are from its own
# __file__ would otherwise look for them next to the copy.
def _tool_as_rs1a_left_it():
    p = os.path.join(SCRATCH, 'show_buttondrift_as_rs1a_left_it.py')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(left(DRIFT))
    s = importlib.util.spec_from_file_location('_sb_then', p)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    mod.ROOT, mod.TPL = sb.ROOT, sb.TPL
    return mod


sb_then = _tool_as_rs1a_left_it()
'''

BUCKETS_WAS = """def buckets(side, text_of):
    \"\"\"Every classified disagreement, sorted into the six kinds RS-1b
    owns plus the one RS-1a takes. Asked of the scanner, not of a list.\"\"\"
    b = collections.Counter()
    for r in pages_of(side):
        raw = text_of(alv_tree.path_of(r))
        sb.JS_REENABLED = sb.js_reenabled_ids(raw)
        m = sb.markup_of(raw)
        for h in sb._scan(r, m):"""

BUCKETS_NOW = """def buckets(side, text_of, tool=None):
    \"\"\"Every classified disagreement, sorted into the six kinds RS-1b
    owns plus the one RS-1a takes. Asked of the scanner, not of a list.

    `tool` ADDED BY RS-1b: which Show-ButtonDrift to ask. A count ABOUT
    the handover asks sb_then, the one RS-1a left; a count about today
    asks the live one, which is the default.\"\"\"
    s_ = tool or sb
    b = collections.Counter()
    for r in pages_of(side):
        raw = text_of(alv_tree.path_of(r))
        s_.JS_REENABLED = s_.js_reenabled_ids(raw)
        m = s_.markup_of(raw)
        for h in s_._scan(r, m):"""

# ---------------------------------------------------------------------------
# test_retone.py - a control RS-1b EXTENDED rather than removed
# ---------------------------------------------------------------------------
# RE-TONE recorded, by exact class string, that it swapped view_recipe's
# Email button from `btn btn-success share-btn-disabled` to `btn
# action-secondary share-btn-disabled`, and its section 2 checks that the
# new string is still present. RS-1b added `disabled-btn` to that element -
# it is a permanently-off button and base styles .disabled-btn directly - so
# the exact string is no longer in the page while every word of RE-TONE's
# decision still is.
#
# That suite already draws this line for a control a later round DELETED,
# and says why: "a removal is ALLOWED ONLY WHEN IT IS NAMED, and the old
# class must still be absent". A successor gets the same treatment and a
# STRICTER test than the removal case - the old Bootstrap class must still
# be gone AND every class RE-TONE put on the element must still be there, so
# a later round that quietly drops action-secondary still fails.
RETONE_MAP_WAS = """REMOVED_BY = {
    ('preview_imported_recipe.html', 'btn action-primary btn-lg'):
        'RE-1, 3 Oct 2026 - the save moved to the action bar',
}
"""

RETONE_MAP_NOW = """REMOVED_BY = {
    ('preview_imported_recipe.html', 'btn action-primary btn-lg'):
        'RE-1, 3 Oct 2026 - the save moved to the action bar',
}

# AND A CONTROL A LATER ROUND EXTENDED - RS-1b, 14 Oct 2026.
#
# Not removed and not retinted: RS-1b added `disabled-btn` to this element,
# because it is an Email button that is permanently off without the
# permission and base.html styles .disabled-btn directly. So the exact
# class string RE-TONE recorded is no longer a substring of the page, while
# every word of RE-TONE's own decision is still on the element.
#
# SAME RULE AS REMOVED_BY - allowed only when it is NAMED - and a stricter
# test than that one: the old Bootstrap class must still be absent, the
# named successor must be present, and every class RE-TONE put there must
# still be among its names. A round that quietly drops action-secondary
# fails here even with a line in this map.
EXTENDED_BY = {
    ('view_recipe.html', 'btn action-secondary share-btn-disabled'):
        ('btn action-secondary disabled-btn share-btn-disabled',
         'RS-1b, 14 Oct 2026 - .disabled-btn, which base styles '
         'directly, on a button that is off for good'),
}
"""

RETONE_LOOP_WAS = """        gone = (rel, now) in REMOVED_BY
        if gone:
            # Named as removed: the new class may be absent, but the OLD
            # one must not have come back in its place.
            good.append(c == 0 and t.count('class="%s"' % was) == 0)
        else:
            good.append(c >= n)
"""

RETONE_LOOP_NOW = """        gone = (rel, now) in REMOVED_BY
        ext = EXTENDED_BY.get((rel, now))
        if gone:
            # Named as removed: the new class may be absent, but the OLD
            # one must not have come back in its place.
            good.append(c == 0 and t.count('class="%s"' % was) == 0)
        elif ext:
            # Named as extended - RS-1b, 14 Oct 2026. Three things, not
            # one: the successor is there, the Bootstrap class has not
            # come back, and the successor still carries every name this
            # suite recorded.
            succ = ext[0]
            good.append(t.count('class="%s"' % succ) >= n
                        and t.count('class="%s"' % was) == 0
                        and set(now.split()) <= set(succ.split()))
        else:
            good.append(c >= n)
"""

# ---------------------------------------------------------------------------
# Push-PendingChanges.ps1 - the gate itself
# ---------------------------------------------------------------------------
GATE_SAY_WAS = """    Say '  == Show-ButtonDrift.py --strict'
    & python $guard --strict 2>&1 | ForEach-Object { Say ('     ' + $_) }"""
GATE_SAY_NOW = """    Say '  == Show-ButtonDrift.py --strict --recipes'
    & python $guard --strict --recipes 2>&1 | ForEach-Object { Say ('     ' + $_) }"""

GATE_NOTE_WAS = """# A suite proves the pages it was written about.  Show-ButtonDrift --strict
# proves the ones nobody thought to write a check for: it walks every
# template and exits non-zero while ANY button still carries a Bootstrap
# colour class in a place base.html owns.  Cheap, and it is the thing that
# catches the next page somebody adds by copying an old one."""

GATE_NOTE_NOW = """# A suite proves the pages it was written about.  Show-ButtonDrift
# --strict --recipes proves the ones nobody thought to write a check for:
# it exits non-zero while ANY button still carries a Bootstrap colour
# class in a place base.html owns.  Cheap, and it is the thing that
# catches the next page somebody adds by copying an old one.
#
# --recipes SINCE RS-1b, 14 Oct 2026, AND THE FLAG IS THE POINT.  Without
# it this gate asked 117 of the application's 142 pages: the recipe and
# meal-plan side was deferred by name in August, and the sentence above
# said "walks every template" for the whole two months in between.  RS-1a
# took that side's 35 decided buttons and RS-1b the 31 that were left, so
# the flag can go on and the claim can be true.
#
# WHAT IT STILL DOES NOT SEE, written here rather than discovered later:
# seventeen buttons across eight pages carry neither a Bootstrap colour
# this tool LISTS nor a house class, so every census in this project
# passes over them.  Two are `btn-outline-light` on ingredient_families -
# a Bootstrap colour that BOOTSTRAP does not list, which is the blind
# spot the note beside the outline variants warns about, one shade
# further on.  The rest are inline style, btn-link, or a page's own
# class.  Widening the page SCOPE does not widen the VOCABULARY, and
# that is the next thing in this line of work."""

SUITE_WAS = """    'test_recipe_photos.py'
)"""
SUITE_NOW = """    'test_recipe_photos.py',
    'test_recipe_side_b.py'
)"""

CLAIMS_ANCHOR = """    @{ File = 'pages\\templates\\base.html'; Text = '.page-action-buttons .alv-seg > *'; What = 'a segment in an action bar is the bar''s height, not nearly it' },"""

CLAIMS = """    @{ File = 'pages\\templates\\base.html'; Text = '.page-action-buttons .alv-seg > *'; What = 'a segment in an action bar is the bar''s height, not nearly it' },
    # ------------------------------------------------ RS-1b, 14 Oct 2026
    # The recipe side finishes, and the drift gate above runs --recipes.
    # Its own comment claimed it walked every template while it asked 117
    # of 142.
    @{ File = 'Show-ButtonDrift.py'; Text = 'def not_the_verb'; What = 'a named exception is not the page''s verb - a map, because the rule I proposed would have demoted Submit FSR' },
    @{ File = 'Show-ButtonDrift.py'; Text = "'d-flex':"; What = 'and d-flex is off the role register - a layout utility that only ever got one button wrong'; Absent = $true; Code = $true },
    @{ File = 'pages\\templates\\view_recipe.html'; Text = 'btn action-secondary" onclick="printShoppingList()'; What = 'Print and Copy join the three house siblings in the same share row' },
    @{ File = 'pages\\templates\\import_recipe.html'; Text = 'btn action-primary btn-lg'; What = 'and Extract Recipe with AI is the page it sits on' },
    @{ File = 'pages\\templates\\view_meal_plan.html'; Text = 'action-secondary action-danger btn-action-disabled'; What = 'a Delete reads destructive even with no permission to press it' },"""

# ---------------------------------------------------------------------------
# the registers
# ---------------------------------------------------------------------------
TREE_WAS = """    # PX-1, 13 Oct 2026 - the recipe photos get an owner.
    'test_recipe_photos.py',
]"""
TREE_NOW = """    # PX-1, 13 Oct 2026 - the recipe photos get an owner.
    'test_recipe_photos.py',
    # RS-1b, 14 Oct 2026 - the recipe side finishes and the drift
    # gate widens to all 142 pages. Wide from birth: it reads named
    # templates through alv_tree and builds no root of its own.
    'test_recipe_side_b.py',
]"""

ROUNDS_WAS = """    '.bak_pxphotos',
]"""
ROUNDS_NOW = """    '.bak_pxphotos',
    # RS-1b, 14 Oct 2026 - the 31 that were left on the recipe
    # side, and the gate goes to --recipes.
    '.bak_rsb',
]"""


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
    raise SystemExit('RS-1b REFUSED: %s' % msg)


def fit(text, lit):
    """A multi-line anchor, written LF here, converted to whatever THIS
    file mostly uses. PX-1's hazard, carried forward because it is not
    PX-1's hazard: the thirteen templates this round edits are four LF,
    five CRLF and four genuinely mixed. Normalising a file to get a match
    turns a one-line change into a four-thousand-line diff nobody can
    review; refusing to match is only marginally better. Single-line
    anchors are left exactly alone."""
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(lit)
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, was, now, where):
    w = fit(text, was)
    once(text, w, where)
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
    # ALREADY APPLIED COMES FIRST, before a single anchor is looked for,
    # and it is asked of the TREE rather than of a marker: if no page
    # still carries one of the thirty-one old open tags, the markup half
    # of this round is done.
    live = 0
    for page, old, _new, _what in EDITS:
        live += read(alv_tree.path_of(page)).count(old)
    if not live:
        print('RS-1b  already applied - no recipe-side button is '
              'undecided or drifting.')
        return 0

    # ---------------------------------------------------------------- 1
    # the thirty-one class lists
    out = {}
    pages = set()
    for page, old, new, what in EDITS:
        p = alv_tree.path_of(page)
        s = out.get(p, read(p))
        once(s, old, '%s (%s)' % (page, what))
        out[p] = s.replace(old, new, 1)
        pages.add(page)

    if (len(EDITS), len(pages)) != (N_EDITS, N_PAGES):
        refuse('expected %d edit(s) on %d page(s); planned %d on %d'
               % (N_EDITS, N_PAGES, len(EDITS), len(pages)))

    # ---------------------------------------------------------------- 2
    # Show-ButtonDrift.py
    p = os.path.join(root, DRIFT)
    s = read(p)
    if 'not_the_verb' in s:
        refuse('%s already carries not_the_verb' % DRIFT)
    s = swap(s, DFLEX_WAS, DFLEX_NOW, '%s (d-flex off DECIDED)' % DRIFT)
    once(s, NTV_ANCHOR, '%s (the map goes above the footer vocabulary)' % DRIFT)
    s = s.replace(NTV_ANCHOR, NTV, 1)
    s = swap(s, PLAN_WAS, PLAN_NOW, '%s (plan_bar takes the page)' % DRIFT)
    s = swap(s, REAL_WAS, REAL_NOW, '%s (the lone-verb rule)' % DRIFT)
    s = swap(s, SCAN1_WAS, SCAN1_NOW, '%s (the bar call site)' % DRIFT)
    s = swap(s, SCAN2_WAS, SCAN2_NOW, '%s (the loose call site)' % DRIFT)
    out[p] = s

    # ---------------------------------------------------------------- 3
    # test_button_sweep.py - the second copy of the rule
    p = os.path.join(root, SWEEP)
    s = read(p)
    s = swap(s, LONE_WAS, LONE_NOW, '%s (section 9, the lone-verb rule)' % SWEEP)
    out[p] = s

    # --------------------------------------------------------------- 3b
    # RS-1a's suite, repaired - the seventh occurrence of the lesson
    p = os.path.join(root, TONES)
    s = read(p)
    if 'as_rs1a_left_it' in s:
        refuse('%s already carries the repair' % TONES)
    s = swap(s, TONES_READER_ANCHOR, TONES_READER,
             '%s (the snapshot reader)' % TONES)
    s = swap(s, TOOL_ANCHOR, TOOL_NOW, '%s (the tool of its time)' % TONES)
    s = swap(s, BUCKETS_WAS, BUCKETS_NOW, '%s (buckets takes a tool)' % TONES)
    s = swap(s, TONES_B2_WAS, TONES_B2_NOW, '%s (section 2)' % TONES)
    s = swap(s, TONES_SWEPT_WAS, TONES_SWEPT_NOW,
             '%s (the swept-side control)' % TONES)
    s = swap(s, TONES_GATE_WAS, TONES_GATE_NOW, '%s (the gate claim)' % TONES)
    out[p] = s

    # --------------------------------------------------------------- 3c
    # RE-TONE's suite - a control this round extended, named as such
    p = os.path.join(root, RETONE)
    s = read(p)
    if 'EXTENDED_BY' in s:
        refuse('%s already carries EXTENDED_BY' % RETONE)
    s = swap(s, RETONE_MAP_WAS, RETONE_MAP_NOW, '%s (the map)' % RETONE)
    s = swap(s, RETONE_LOOP_WAS, RETONE_LOOP_NOW, '%s (the loop)' % RETONE)
    out[p] = s

    # ---------------------------------------------------------------- 4
    # the gate
    p = os.path.join(root, PS1)
    s = read(p)
    if '--strict --recipes' in s:
        refuse('%s already runs the drift guard with --recipes' % PS1)
    s = swap(s, GATE_NOTE_WAS, GATE_NOTE_NOW, '%s (the gate note)' % PS1)
    s = swap(s, GATE_SAY_WAS, GATE_SAY_NOW, '%s (the gate itself)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, CLAIMS_ANCHOR, CLAIMS, '%s (the claims)' % PS1)
    out[p] = s

    # ---------------------------------------------------------------- 5
    # the registers, and the two counters these rounds keep by hand
    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'RS-1b, 14 Oct 2026 - this round own suite. '
                  'test_button_sweep is still NOT released: its markup walk '
                  'rebuilds a pre-sweep tree and stays narrow by design, '
                  'which is why the GATE widened and the SUITE did not.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'RS-1b, 14 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('RS-1b --check  %d file(s) would change, %d class list(s) '
              'on %d page(s)' % (len(out), N_EDITS, N_PAGES))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('RS-1b applied.')
    print('   %d class list(s) on %d page(s)  '
          '(%d drifting, %d never decided)'
          % (N_EDITS, N_PAGES, N_DRIFT, N_DECIDED))
    print("   d-flex off the role register, NOT_THE_VERB on it")
    print('   the drift gate goes from %d page(s) to %d'
          % (GATE_WAS, GATE_NOW))
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
