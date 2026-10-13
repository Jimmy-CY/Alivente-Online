# -*- coding: utf-8 -*-
"""apply_recipe_tones.py - round RS-1a, 13 Oct 2026.

THE REST OF THE APPLICATION CATCHES UP.

The recipe and personal side has been excluded from the button sweep BY
NAME since August - `templates()` ends with

    if not include_recipes and is_recipe_side(rel): continue

and the push gate calls Show-ButtonDrift.py --strict without --recipes,
so its corpus is 117 of the application's 142 pages. The comment sitting
directly above that call says the guard

    walks every template and exits non-zero while ANY button still
    carries a Bootstrap colour class

It walks 117 of 142. That is the fifth time this week that a claim about
everything turned out to be a claim about a subset - E-10, X0, E11's
section 10, E11's own first-draft suite, and now the push gate's own
prose. It is not fixed here: RS-1a takes the tones, RS-1b takes what is
left and THEN widens the gate, because --strict exits non-zero on an
undecided button as well as on drift, so the gate can only be widened on
the day both are zero.

WHAT RS-1a IS
--------------
The 35 buttons on the recipe side where a Bootstrap colour is PRESENT.
That is one cause, not a count somebody chose, and it is the whole of
what this round touches.

    20  btn btn-secondary        -> btn action-secondary
     4  btn btn-danger           -> btn action-secondary action-danger
     3  btn btn-info             -> btn action-primary
     3  btn btn-primary          -> btn action-primary
     2  btn btn-outline-danger   -> btn action-secondary
     1  btn btn-outline-primary  -> btn action-secondary
     1  btn btn-info text-white  -> btn action-primary text-white
     1  btn btn-secondary        -> btn action-primary

35 elements, 28 distinct open tags, 11 pages.

RENDERED, NOT READ
-------------------
Bootstrap 4.1.3 + base.html + the page own style block, in a
.modal-footer, at 1280 and 390:

    btn-secondary      solid grey, white ink  4.69  ->  white, ink 12.95
    btn-danger         solid red              4.53  ->  white, red ink 6.54
    btn-primary        BOOTSTRAP BLUE         3.98  ->  teal 4.91
    btn-outline-primary blue ink              3.98  ->  ink 12.95
    btn-info           teal rgb(14,124,139)   4.91  ->  IDENTICAL
    btn-outline-danger red ink                4.53  ->  ink 12.95

31 of the 35 move visibly. FOUR of them are under 4.5:1 today and all
four clear it afterwards. FOUR more do not move at all - base recolours
.btn-info to the accent on purpose, so those are a naming defect, the
same finding E11 made about the same class.

NO TAP TARGET CLAIM IS AVAILABLE HERE, and it was measured before being
left out: every one of these already renders at 44px on a phone inside a
modal footer.

THESE ARE JOINING A LOOK THAT ALREADY EXISTS
---------------------------------------------
Asked of the already-swept side, in modal footers:

    Cancel dressed as btn action-secondary          57 of 57, 34 pages
    destructive buttons carrying action-danger              14
    footer primaries carrying action-primary                32

The survey first said 13 and 27. Those were the TOP ROWS of a tally, not
its totals - one more footer carries action-danger alongside a page hook,
and five more carry action-primary the same way. Counted by TOKEN rather
than by whole class string, which is the only count that means anything
when a page adds a hook of its own.

So the 20 Cancels and the 4 Deletes are not a new design decision. They
are the rest of the application catching up to 57 and 13 precedents.

THE TWO DECISIONS DEMETRI TOOK
-------------------------------
1. The two btn-outline-danger Reset buttons GO GREY, not red. A Reset
   clears a form or a filter; action-danger is for removing a record.
   Measured: red ink 4.53 becomes ink 12.95, and the red is deliberately
   given up.

2. The split itself. RS-1a is the 35 where a Bootstrap colour is
   present; everything else waits for RS-1b.

ONE OF THE 35 LOOKED WRONG AND WAS CHECKED
-------------------------------------------
view_recipe.html line 2343, a grey btn-secondary the classifier wants to
make the PRIMARY. Read: it is Print Schedule, in a modal footer whose
only other control is Close. It is that modal verb, and 27 footer
primaries on the swept side are dressed exactly that way. Promoted.

WHAT THIS ROUND REFUSES TO TOUCH, AND ASSERTS IT DID NOT
---------------------------------------------------------
Measured as zero overlap before the round was written: not one of the 35
also needs anything RS-1b owns. So the patcher gates on all of these
being UNCHANGED afterwards:

     8  the house disabled marker is missing
     4  the class list is only REORDERED - real, by the house own rule,
        and invisible. Asked of the swept side: 0 of 509 classified hits
        are order-only disagreements, so canonical order IS the standard
     2  action-danger added to a button labelled Delete
     7  promotions, FOUR of which the classifier gets wrong - three are
        links to another page and one is a view toggle whose decision is
        written in a comment above it
     1  a demotion, which is wrong - it is pantry_staples own verb
    13  UNCLASSIFIED

See test_recipe_tones.py.
"""
import os
import sys

import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_rstones'
SUITE = 'test_recipe_tones.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

N_ELEMENTS, N_GROUPS, N_PAGES = 35, 28, 11

# What must NOT move. RS-1b owns every one of these.
LEFT_DISABLED, LEFT_REORDER, LEFT_DANGER_ADD = 8, 4, 2
LEFT_PROMOTE, LEFT_DEMOTE, LEFT_UNCLASSIFIED = 7, 1, 13

CEILING_WAS, CEILING_NOW = 38, 38
CONVERTED_WAS, CONVERTED_NOW = 72, 73
WAITING_WAS, WAITING_NOW = 2, 2
ALIAS_WAS, ALIAS_NOW = 55, 57

EDITS = (
    ('create_meal_plan.html',
     '<button class="btn btn-outline-primary" onclick="loadMoreRecipesInSelector()">',
     '<button class="btn action-secondary" onclick="loadMoreRecipesInSelector()">',
     1, 'Show More'),
    ('ingredient_families.html',
     '<button type="submit" class="btn btn-outline-danger">',
     '<button type="submit" class="btn action-secondary">',
     1, 'Reset'),
    ('ingredient_families.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     2, 'Cancel'),
    ('ingredient_families.html',
     '<button type="submit" class="btn btn-info text-white">',
     '<button type="submit" class="btn action-primary text-white">',
     1, 'Save changes'),
    ('meal_plan_calendar.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     3, 'Cancel'),
    ('meal_plan_calendar.html',
     '<button type="submit" class="btn btn-danger">',
     '<button type="submit" class="btn action-secondary action-danger">',
     1, 'Delete Meal Plan'),
    ('meal_plan_calendar.html',
     '<button type="submit" class="btn btn-info">',
     '<button type="submit" class="btn action-primary">',
     1, 'Duplicate Meal Plan'),
    ('meal_plan_calendar.html',
     '<button type="button" class="btn btn-primary" id="confirmAddRecipeBtn" disabled onclick="confirmAddRecipe()">',
     '<button type="button" class="btn action-primary" id="confirmAddRecipeBtn" disabled onclick="confirmAddRecipe()">',
     1, 'Add Recipe'),
    ('meal_plans.html',
     '<button type="button" class="btn btn-secondary" onclick="$(\'#deleteModal\').modal(\'hide\');">',
     '<button type="button" class="btn action-secondary" onclick="$(\'#deleteModal\').modal(\'hide\');">',
     1, 'Cancel'),
    ('meal_plans.html',
     '<button type="submit" class="btn btn-danger">',
     '<button type="submit" class="btn action-secondary action-danger">',
     1, 'Delete Meal Plan'),
    ('meal_plans.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     1, 'Cancel'),
    ('meal_plans.html',
     '<button type="submit" class="btn btn-info">',
     '<button type="submit" class="btn action-primary">',
     1, 'Duplicate Meal Plan'),
    ('measurement_units_management.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     1, 'Cancel'),
    ('pantry_staples.html',
     '<button type="submit" class="btn btn-outline-danger">',
     '<button type="submit" class="btn action-secondary">',
     1, 'Reset'),
    ('recipe_management.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     1, 'Cancel'),
    ('recipe_management.html',
     '<button type="submit" class="btn btn-danger">',
     '<button type="submit" class="btn action-secondary action-danger">',
     1, 'Delete Recipe'),
    ('unit_conversions_management.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     3, 'Cancel'),
    ('unit_conversions_management.html',
     '<button type="button" class="btn btn-primary" onclick="saveEditConversion()">',
     '<button type="button" class="btn action-primary" onclick="saveEditConversion()">',
     1, 'Update Conversion'),
    ('view_meal_plan.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     2, 'Cancel'),
    ('view_meal_plan.html',
     '<button type="submit" class="btn btn-danger">',
     '<button type="submit" class="btn action-secondary action-danger">',
     1, 'Delete Meal Plan'),
    ('view_meal_plan.html',
     '<button type="submit" class="btn btn-info">',
     '<button type="submit" class="btn action-primary">',
     1, 'Duplicate Meal Plan'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal" id="conversionMiniCancel">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal" id="conversionMiniCancel">',
     1, 'Cancel'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     2, 'Close'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-secondary" onclick="printCookingSchedule()">',
     '<button type="button" class="btn action-primary" onclick="printCookingSchedule()">',
     1, 'Print Schedule'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal" id="cancelBtn">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal" id="cancelBtn">',
     1, 'Cancel'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal" id="doneBtn" style="display: none;">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal" id="doneBtn" style="display: none;">',
     1, 'Done'),
    ('view_recipe.html',
     '<button type="button" class="btn btn-primary" onclick="nextStep()" id="nextBtn">',
     '<button type="button" class="btn action-primary" onclick="nextStep()" id="nextBtn">',
     1, 'Next'),
    ('wcim_recipe_quick_view.html',
     '<button type="button" class="btn btn-secondary" data-dismiss="modal">',
     '<button type="button" class="btn action-secondary" data-dismiss="modal">',
     1, 'Close'),
)


# ---------------------------------------------------------------------------
# E11's SUITE, REPAIRED. Four checks it wrote two hours earlier read a
# SNAPSHOT LIVE, and RS-1a is the round that moved what they read.
# MH-2 did exactly this for DB-5's suite yesterday, for the same
# reason, and E11's own docstring states the rule it then broke.
# ---------------------------------------------------------------------------
JS = 'test_js_buttons.py'

JS_REPAIRS = (
    ('n_markup = (ma.count(\'class="btn btn-secondary"\')\n            + ma.count(\'class="btn btn-primary"\'))\nok(n_markup == MGT_MARKUP_BOOT,\n   \'%s keeps its %d Bootstrap-toned button(s) IN MARKUP - they belong to \'\n   \'the recipe-side sweep\' % (MGT[:28], MGT_MARKUP_BOOT),\n   \'%d found\' % n_markup)\nok(mb.count(\'class="btn btn-secondary"\') == ma.count(\n       \'class="btn btn-secondary"\')\n   and mb.count(\'class="btn btn-primary"\') == ma.count(\n       \'class="btn btn-primary"\'),\n   \'  and not one of them moved\')',
     '# REPAIRED BY RS-1a, 13 Oct 2026. THIS WAS READ LIVE AND IT IS A\n# SNAPSHOT. The claim is "E11 did not touch this page\'s markup", which\n# is a fact about the day E11 ran - and RS-1a then converted all four of\n# those buttons, because they were four of its thirty-five. Read live,\n# E11\'s own suite reported that E11 had done something it did not.\n#\n# Sixth time this distinction has bitten in this project, and the first\n# where the round that made the mistake had the rule written in its own\n# docstring. It did not fail E11\'s sweep because nothing had moved yet;\n# it failed the moment the next round landed, which is the sweep working\n# and the round not.\nml = left_page(MGT)\nn_markup = (ml.count(\'class="btn btn-secondary"\')\n            + ml.count(\'class="btn btn-primary"\'))\nok(n_markup == MGT_MARKUP_BOOT,\n   \'%s kept its %d Bootstrap-toned button(s) IN MARKUP - read as E11 \'\n   \'left it; RS-1a took them later\' % (MGT[:28], MGT_MARKUP_BOOT),\n   \'%d found\' % n_markup)\nok(mb.count(\'class="btn btn-secondary"\') == ml.count(\n       \'class="btn btn-secondary"\')\n   and mb.count(\'class="btn btn-primary"\') == ml.count(\n       \'class="btn btn-primary"\'),\n   \'  and E11 moved none of them\')'),
    ("ok(len(alv_tree.CONVERTED) == CONVERTED_NOW,\n   'CONVERTED holds %d' % CONVERTED_NOW, len(alv_tree.CONVERTED))",
     "# REPAIRED BY RS-1a: this was `==`, which is a snapshot dressed as an\n# invariant - every later round moves the register. What is true for\n# ever is that E11 ADDED one and the register never shrinks past it; the\n# exact number E11 left is asked of the pin below, through as_left_by.\nok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,\n   'CONVERTED holds at least the %d E11 left' % CONVERTED_NOW,\n   len(alv_tree.CONVERTED))"),
    ("ok(ROUNDS and ROUNDS[-1] == SUFFIX,\n   '%s is last in alv_rounds.ROUNDS' % SUFFIX,\n   ROUNDS[-3:] if ROUNDS else 'empty')",
     '# REPAIRED BY RS-1a: "last" is true until the next round appends. What\n# the order has to say is that this round comes AFTER the one before it,\n# which is what as_left_by walks.\nok(SUFFIX in ROUNDS and \'.bak_surfborder\' in ROUNDS\n   and ROUNDS.index(SUFFIX) > ROUNDS.index(\'.bak_surfborder\'),\n   \'%s sits after .bak_surfborder in alv_rounds.ROUNDS\' % SUFFIX,\n   ROUNDS[-4:] if ROUNDS else \'empty\')'),
    ('def left(name):',
     'def left_page(rel):\n    """A TEMPLATE as E11 left it. left() above is for repo-root files;\n    a page needs alv_tree.path_of first, and RS-1a is the round that\n    found out this suite needed it at all."""\n    p = alv_tree.path_of(rel)\n    if as_left_by is None:\n        return read(p)\n    return as_left_by(p, SUFFIX, read)\n\n\ndef left(name):'),
)

# ---------------------------------------------------------------------------
# F2b's SUITE, REPAIRED - the same fault one round further back.
# Its render read the AFTER side live, so it compared F2b's backup
# against the page as it is TODAY. RS-1a converted one Cancel on
# recipe_management - one of F2b's six rendered pages - and F2b's suite
# reported a background-color and two text-fill colours as F2b's own.
# ---------------------------------------------------------------------------
FB = 'test_surface_border.py'

FB_REPAIRS = (
    ('def touched():\n    return [p for p in alv_tree.templates() if os.path.isfile(p + SUFFIX)]',
     "# ADDED BY RS-1a, 13 Oct 2026 - THE PAGE AS F2b LEFT IT, which is not\n# the same as the page today. was() above is the before side and was\n# always right. The AFTER side of the render was read LIVE, so this\n# suite compared F2b's backup against whatever the page looks like now\n# - and the first later round to touch any of the six rendered pages\n# had its change reported as F2b's. RS-1a converted one Cancel on\n# recipe_management and this suite duly failed with a background-color\n# and two text-fill colours that F2b never moved.\n#\n# FIFTH occurrence of the as_left_by lesson. This file documents the\n# fourth, in its own section 6.\ndef as_f2b_left_it(p):\n    if as_left_by is None:\n        return read(p)\n    return as_left_by(p, SUFFIX, read)\n\n\ndef touched():\n    return [p for p in alv_tree.templates() if os.path.isfile(p + SUFFIX)]"),
    ("            for tag, text in (('before', was(p)), ('after', read(p))):",
     "            # REPAIRED BY RS-1a: the after side was read(p), live.\n            for tag, text in (('before', was(p)),\n                              ('after', as_f2b_left_it(p))):"),
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
    raise SystemExit('RS-1a REFUSED: %s' % msg)


def exactly(text, lit, n, where):
    """A group is matched EXACTLY n times. Twenty of the thirty-five are
    the same Cancel tag repeated, so `once` is the wrong gate here - but
    an UNCOUNTED replace is how a sweep reaches a button nobody looked
    at. Measured before the round was written: every distinct open tag
    appears in its own file exactly as many times as it is a hit, and
    every repeat wants the same replacement."""
    got = text.count(lit)
    if got != n:
        refuse('%s: %r appears %d time(s), expected exactly %d'
               % (where, lit[:66], got, n))


def bump(text, lit, was, now, note, where):
    old = lit % was
    exactly(text, old, 1, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, before a single anchor is looked for,
    # and it is asked of the TREE: if no page still carries one of the
    # old open tags, the round is done.
    live = 0
    for page, old, _new, _n, _what in EDITS:
        p = alv_tree.path_of(page)
        live += read(p).count(old)
    if not live:
        print('RS-1a  already applied - no recipe-side button wears a '
              'Bootstrap tone.')
        return 0

    out = {}
    done, pages, groups = 0, set(), 0
    for page, old, new, n, what in EDITS:
        p = alv_tree.path_of(page)
        s = out.get(p, read(p))
        exactly(s, old, n, '%s (%s)' % (page, what))
        out[p] = s.replace(old, new)
        done += n
        groups += 1
        pages.add(page)

    if (done, groups, len(pages)) != (N_ELEMENTS, N_GROUPS, N_PAGES):
        refuse('expected %d element(s) in %d group(s) on %d page(s); '
               'planned %d in %d on %d'
               % (N_ELEMENTS, N_GROUPS, N_PAGES, done, groups, len(pages)))

    # ---------------------------------------------------------------- 1
    # E11's suite and F2b's suite, repaired
    p = os.path.join(root, JS)
    s = read(p)
    for was_, now_ in JS_REPAIRS:
        exactly(s, was_, 1, '%s (a live read of a snapshot)' % JS)
        s = s.replace(was_, now_, 1)
    out[p] = s

    for name, reps in ((FB, FB_REPAIRS),):
        p = os.path.join(root, name)
        s = read(p)
        for was_, now_ in reps:
            exactly(s, was_, 1,
                    '%s (a live read of a snapshot)' % name)
            s = s.replace(was_, now_, 1)
        out[p] = s

    # ---------------------------------------------------------------- 2
    # the registers
    p = os.path.join(root, TREE)
    s = read(p)
    anchor = ("    # E11, 13 Oct 2026 - the script census gets an owner.\n"
              "    'test_js_buttons.py',\n]")
    exactly(s, anchor, 1, '%s (CONVERTED)' % TREE)
    out[p] = s.replace(
        anchor,
        ("    # E11, 13 Oct 2026 - the script census gets an owner.\n"
         "    'test_js_buttons.py',\n"
         "    # RS-1a, 13 Oct 2026 - the recipe side starts catching up.\n"
         "    '%s',\n]" % SUITE), 1)

    p = os.path.join(root, ROUNDS)
    s = read(p)
    anchor = "    '.bak_jsbtn',\n]"
    exactly(s, anchor, 1, '%s (ROUNDS)' % ROUNDS)
    out[p] = s.replace(anchor,
                       "    '.bak_jsbtn',\n    '%s',\n]" % SUFFIX, 1)

    p = os.path.join(root, WD)
    s = read(p)
    out[p] = bump(s, 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'RS-1a, 13 Oct 2026 - this round own suite. The recipe '
                  'side is not released: RS-1b takes what is left and then '
                  'widens the gate.', '%s (CONVERTED_N)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    old = "ok(len(aliased) == %d," % ALIAS_WAS
    exactly(s, old, 1, '%s (alias count)' % CO)
    s = s.replace(old, "ok(len(aliased) == %d," % ALIAS_NOW, 1)
    old2 = ("'%d file(s) alias it - 27 patchers and 28 suites' "
            "% len(aliased),")
    exactly(s, old2, 1, '%s (alias wording)' % CO)
    s = s.replace(old2,
                  ("'%d file(s) alias it - 28 patchers and 29 suites' "
                   "% len(aliased),   # RS-1a, 13 Oct 2026 - this round own "
                   "patcher and suite   # (was " + str(ALIAS_WAS)
                   + ", 27 and 28)"), 1)
    out[p] = s

    p = os.path.join(root, PS1)
    s = read(p)
    anchor = "    'test_js_buttons.py'\n)"
    exactly(s, anchor, 1, '%s ($suites)' % PS1)
    out[p] = s.replace(anchor,
                       "    'test_js_buttons.py',\n    '%s'\n)" % SUITE, 1)

    # ---------------------------------------------------------------- 3
    if CHECK:
        print('RS-1a  --check: %d file(s) would change' % len(out))
        for q in sorted(out):
            print('        %s' % os.path.relpath(q, root))
        print('      %d element(s), %d group(s), %d page(s)'
              % (N_ELEMENTS, N_GROUPS, N_PAGES))
        print('      LEFT for RS-1b: %d disabled, %d reorder, %d danger-add, '
              '%d promote, %d demote, %d unclassified'
              % (LEFT_DISABLED, LEFT_REORDER, LEFT_DANGER_ADD,
                 LEFT_PROMOTE, LEFT_DEMOTE, LEFT_UNCLASSIFIED))
        print('      CONVERTED %d -> %d; WAITING %d; ceiling %d; '
              'aliases %d -> %d'
              % (CONVERTED_WAS, CONVERTED_NOW, WAITING_NOW, CEILING_NOW,
                 ALIAS_WAS, ALIAS_NOW))
        return 0

    for q in sorted(out):
        backup(q)
        write(q, out[q])
    print('RS-1a  applied to %d file(s).' % len(out))
    print('     %d recipe-side button(s) on %d page(s) off Bootstrap '
          'colours.' % (N_ELEMENTS, N_PAGES))
    print('     31 move visibly; 4 do not, because base already recolours '
          '.btn-info to the accent.')
    print('     Nothing RS-1b owns was touched - the suite asserts all six '
          'of those counts.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
