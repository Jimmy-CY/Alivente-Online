# -*- coding: utf-8 -*-
"""SECTION R, ROUND R1 - TONE BY CONSEQUENCE, ACROSS THE RECIPES CLUSTER

The last of the green. Forty-five controls wear Bootstrap's btn-success,
btn-warning or btn-outline-success, and base's standards block says why
they were left alone until somebody decided what each one MEANS:

    THE BUTTON FAMILIES ARE DELIBERATELY NOT ANSWERED. btn-success,
    btn-warning and btn-outline-success are worn 52 times and not once as
    a status - they are Save, Add, Create, Generate, Email, Continue,
    Edit. Giving them a house tint would make drift look deliberate and
    hide it from Show-ButtonDrift.py. An action takes .action-primary or
    .action-secondary, BY WEIGHT.

So this round does not tint anything. It reads each control and gives it
the weight its consequence deserves, which is the rule Demetri agreed for
CRS and again for the mapping delivered on 29 Sep.

WHERE THEY ARE. Every one is in the Recipes / Meal Plans / Units cluster
plus a few strays - one module's habit, not a house-wide drift.

ELEVEN NEEDED NO DECISION AT ALL: they already wear the right house class
AND the Bootstrap one on the same element, so the green is painted on top
of a button that is already correct. For those the round deletes the
Bootstrap family and nothing else changes but the colour.

NOTHING IN THIS ROUND IS DESTRUCTIVE, so no control here becomes
.action-danger - worth stating, because in CRS tone-by-consequence moved
Close Submission to danger. There is no equivalent in Recipes.

THE TWO DEMETRI WAS ASKED ABOUT, and answered on 30 Sep:

    title_deeds_management - View. It opens a document from a table row,
    and the house does that with an icon: .icon-action-btn .icon-view,
    used 14 times elsewhere, seven of them with a document-specific icon
    rather than an eye. It keeps fa-scroll and gains a title, and it is
    already sitting in a .desktop-action-cell, which is where row actions
    belong.

    wcim_results - Try again. It starts the search over rather than
    committing anything, so .action-secondary.

AND TWO THINGS THAT ARE NOT BUTTONS:

    user_administration builds a confirm button IN JAVASCRIPT - Enable
    gets btn-success, Disable btn-danger. Enable is an ordinary commit
    and takes .action-primary; Disable takes .action-danger, which the
    house already has and which says the same thing btn-danger was
    saying.

    personal_notification_settings declares `.notification-card
    .btn-success` and has NO btn-success element on it at all. A dead
    rule. It goes.

REPORTED, NOT CHANGED: property_assets wears btn-outline-success three
times on buttons welded into an input group, where Bootstrap owns the
geometry - the category Show-ButtonDrift already excludes by name. And
the confirm modal in user_administration paints its own header
`bg-success` / `bg-danger` where base has .alv-modal-head and
.alv-modal-head--danger. That is a component question, not a button one.

Backups: .bak_retone. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_retone'
CRLF = {}

FAM = re.compile(r'\bbtn-(?:outline-)?(?:success|warning)\b')

CLASSES = {
    'create_meal_plan.html': [
        ('btn btn-success action-primary',
         'btn action-primary', 2, 'Create Meal Plan / Update Meal Plan'),
    ],
    'ingredient_families.html': [
        ('btn btn-success',
         'btn action-primary', 1, 'Create family'),
        ('btn btn-success btn-sm',
         'btn action-secondary btn-sm', 1, 'Add'),
    ],
    'map_ingredients_nutrition.html': [
        ('btn btn-success',
         'btn action-secondary', 1, '${SCOPED_RETURN_LABEL}'),
    ],
    'meal_plan_calendar.html': [
        ('btn btn-success action-primary',
         'btn action-primary', 1, 'New Meal Plan'),
        ('btn btn-success btn-lg',
         'btn action-primary btn-lg', 1, 'Create Meal Plan for This Week'),
    ],
    'meal_plan_shopping_list.html': [
        ('btn btn-success',
         'btn action-primary', 3, 'Done / Generate List / Save Conversions & Generate List'),
    ],
    'measurement_units_management.html': [
        ('btn btn-success',
         'btn action-primary', 1, 'Add Unit'),
        ('btn btn-success action-primary',
         'btn action-primary', 2, 'Add Measurement Unit'),
    ],
    'pantry_staples.html': [
        ('btn btn-success',
         'btn action-primary', 1, 'Add Staple'),
    ],
    'preview_imported_recipe.html': [
        ('btn btn-success',
         'btn action-secondary', 2, 'Add Ingredient / Add Measurement'),
        ('btn btn-success action-primary',
         'btn action-primary', 1, 'View Recipe'),
        ('btn btn-success btn-lg',
         'btn action-primary btn-lg', 1, 'Save Recipe'),
    ],
    'unit_conversions_management.html': [
        ('btn btn-success',
         'btn action-primary', 2, 'Save All Conversions / Save Conversion'),
        ('btn btn-success action-more-btn',
         'btn action-more-btn', 1, '(icon only)'),
        ('btn btn-success action-primary',
         'btn action-primary', 2, 'Add New Conversion'),
        ('btn btn-warning action-secondary',
         'btn action-secondary', 2, 'Missing Conversions ({{ missing_co'),
    ],
    'view_meal_plan.html': [
        ('btn btn-success action-more-btn',
         'btn action-more-btn', 1, '(icon only)'),
        ('btn btn-success action-primary',
         'btn action-primary', 1, 'Shopping List'),
        ('btn btn-warning action-secondary',
         'btn action-secondary', 1, 'Edit'),
    ],
    'view_recipe.html': [
        ('btn btn-success',
         'btn action-secondary', 2, 'Email / WhatsApp'),
        ('btn btn-success action-secondary',
         'btn action-secondary', 2, 'Nutrition / Shopping List'),
        ('btn btn-success share-btn-disabled',
         'btn action-secondary share-btn-disabled', 1, 'Email'),
        ('btn btn-warning',
         'btn action-primary', 1, 'Save & Recalculate'),
        ('btn btn-warning action-more-btn',
         'btn action-more-btn', 1, '(icon only)'),
        ('btn btn-warning action-primary',
         'btn action-primary', 1, 'Edit Recipe'),
        ('btn btn-warning action-primary btn-action-disabled',
         'btn action-primary btn-action-disabled', 1, 'Edit Recipe'),
    ],
    'wcim_extras.html': [
        ('btn btn-success',
         'btn action-primary', 1, 'Show recipes'),
    ],
    'wcim_landing.html': [
        ('btn btn-success',
         'btn action-primary', 1, 'Continue'),
    ],
    'wcim_recipe_quick_view.html': [
        ('btn btn-outline-success',
         'btn action-secondary', 1, 'Open full recipe'),
    ],
    'wcim_results.html': [
        ('btn btn-success',
         'btn action-secondary', 1, 'Try again'),
    ],
}


# The row action that replaces a green word-button in a table cell.
DEEDS = 'title_deeds_management.html'
DEEDS_WAS = """<button type="button" class="btn btn-sm btn-success" onclick="viewDocument('{{ property.prop_title_deed.url }}', '{{ property.prop_title_deed.name }}', '{{ property.prop_name }}')">
                    <i class="fas fa-scroll"></i> View
                </button>"""
DEEDS_NOW = """<button type="button" class="icon-action-btn icon-view" title="View title deed" aria-label="View title deed" onclick="viewDocument('{{ property.prop_title_deed.url }}', '{{ property.prop_title_deed.name }}', '{{ property.prop_name }}')">
                    <i class="fas fa-scroll"></i>
                </button>"""

# The confirm button this page builds in script rather than in markup.
ADMIN = 'user_administration.html'
ADMIN_SWAPS = [
    ("submitBtn.className = 'btn btn-success';",
     "submitBtn.className = 'btn action-primary';",
     'Enable is an ordinary commit'),
    ("submitBtn.className = 'btn btn-danger';",
     "submitBtn.className = 'btn action-danger';",
     '  and Disable is the destructive one, which the house has a class '
     'for'),
]

# A rule for a class that is not on the page.
NOTIF = 'personal_notification_settings.html'
NOTIF_WAS = """    /* Save button full-width on mobile */
    .notification-card .btn-success {
        width: 100%;
        padding: 10px 12px;
    }"""
NOTIF_NOW = """    /* THE SAVE BUTTON FULL-WIDTH ON A PHONE WAS HERE, and it had
       stopped reaching anything. This page's four Save buttons wear
       .action-primary - an earlier round renamed them and left this
       rule pointing at the class they used to have. Measured 30 Sep:
       zero btn-success elements on the page.

       AND base SAYS IT ANYWAY, for the class they wear now:
       .page-action-buttons .action-primary takes flex 1 1 auto below
       768px, which is the primary taking the width. Dead twice over.
                                                   [test_retone.py] */"""

LEFT = 'property_assets.html'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('R1: %s is not a byte copy' % bak)


def nocom(t):
    t = re.sub(r'<!--.*?-->|\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


# ==========================================================================
print('=' * 74)
print('SECTION R, ROUND R1 - TONE BY CONSEQUENCE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

moved = 0
for rel in sorted(CLASSES):
    q = alv_tree.join(rel.replace('/', os.sep))
    t, raw = read(q)
    if not FAM.search(nocom(t)):
        print('  %-34s already done' % rel)
        continue
    done = []
    for was, now, n, what in CLASSES[rel]:
        a = eol(q, 'class="%s"' % was)
        if t.count(a) != n:
            raise SystemExit('R1: %s - class="%s" is there %d time(s), not '
                             '%d' % (rel, was, t.count(a), n))
        t = t.replace(a, eol(q, 'class="%s"' % now))
        done.append('%d x %s -> %s  (%s)'
                    % (n, was.replace('btn ', ''), now.replace('btn ', ''),
                       what))
        moved += n
    # GATE: nothing of the family may survive outside a comment.
    if FAM.search(nocom(t)):
        raise SystemExit('R1: %s still wears a Bootstrap tone: %s'
                         % (rel, FAM.findall(nocom(t))[:3]))
    print('  %s' % rel)
    for d in done:
        print('     %s' % d)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- the row action -----------------------------------------------------
q = alv_tree.join(DEEDS)
t, raw = read(q)
print('  %s' % DEEDS)
if 'icon-action-btn' in t:
    print('     already a row action')
else:
    a = eol(q, DEEDS_WAS)
    if t.count(a) != 1:
        raise SystemExit('R1: %s - the View button is there %d time(s), '
                         'not 1' % (DEEDS, t.count(a)))
    t = t.replace(a, eol(q, DEEDS_NOW), 1)
    moved += 1
    print('     the green View becomes the house row action - '
          'icon-action-btn icon-view, in the cell it was already in')
    if FAM.search(nocom(t)):
        raise SystemExit('R1: %s still wears a Bootstrap tone' % DEEDS)
    if 'aria-label' not in eol(q, DEEDS_NOW):
        raise SystemExit('R1: an icon-only control with no label')
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- the button built in script -----------------------------------------
q = alv_tree.join(ADMIN)
t, raw = read(q)
print('  %s' % ADMIN)
if "'btn action-primary'" in t:
    print('     already toned')
else:
    for was, now, what in ADMIN_SWAPS:
        a = eol(q, was)
        if t.count(a) != 1:
            raise SystemExit('R1: %s - %r is there %d time(s), not 1'
                             % (ADMIN, was, t.count(a)))
        t = t.replace(a, eol(q, now), 1)
        print('     %s' % what)
        moved += 1
    if re.search(r"className = 'btn btn-", t):
        raise SystemExit('R1: %s still assigns a Bootstrap tone' % ADMIN)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- the rule with nothing to reach -------------------------------------
q = alv_tree.join(NOTIF)
t, raw = read(q)
print('  %s' % NOTIF)
# THE GUARD MUST NAME WHAT THE ROUND WROTE. The first version looked
# for words that are not in the replacement comment, so it said
# not-done on a page that was finished and the round refused itself.
if 'stopped reaching anything' in t:
    print('     the dead rule is already gone')
else:
    n_el = len(re.findall(r'class="[^"]*\bbtn-success\b', nocom(t)))
    if n_el:
        raise SystemExit('R1: %s has %d btn-success element(s) after all - '
                         'the rule is not dead' % (NOTIF, n_el))
    a = eol(q, NOTIF_WAS)
    if t.count(a) != 1:
        raise SystemExit('R1: %s - the rule is there %d time(s), not 1'
                         % (NOTIF, t.count(a)))
    t = t.replace(a, eol(q, NOTIF_NOW), 1)
    print('     a rule for a class this page does not have, measured at '
          'zero elements')
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- what is left, on purpose -------------------------------------------
t = read(alv_tree.join(LEFT))[0]
n = len(FAM.findall(nocom(t)))
print('  reported, not changed')
print('     %-34s keeps %d btn-outline-success - buttons welded into an '
      'input group,' % (LEFT, n))
print('     %-34s where Bootstrap owns the geometry. The category '
      'Show-ButtonDrift' % '')
print('     %-34s already excludes by name.' % '')
if n != 3:
    raise SystemExit('R1: %s was to KEEP three and has %d' % (LEFT, n))

# ==========================================================================
# THE STANDARDS SUITE COUNTED WHAT THIS ROUND CAME TO REMOVE
#
#   test_good_warn holds base's rule 3.1a - that Bootstrap's info,
#   success and warning FAMILIES are answered by base, and that the
#   BUTTON families deliberately are not. It ends by counting the button
#   uses "left alone, visibly, for their own round", and requiring at
#   least 45.
#
#   This is that round. The floor is now three, and they are named rather
#   than counted - a floor says how many, and by the time three are left
#   it is worth saying WHICH.
#
#   AND IT COUNTED COMMENTS. Reading the raw file, it finds four: the
#   three real ones and the word btn-success inside the comment this
#   round writes on personal_notification_settings explaining that there
#   is no btn-success on the page. Lesson 21, one more time.
# ==========================================================================
GW = 'test_good_warn.py'
GW_WAS = """ok(btn >= 45,
   '  %d button uses are left alone, visibly, for their own round' % btn,
   btn)"""
GW_NOW = """ok(btn == 3,
   '  %d button uses are left, and they are named below - R1 took the '
   'other forty-four on 30 Sep' % btn, btn)
ok(sorted(btn_where) == ['property_assets.html'],
   '  and all three are on property_assets, welded into an input group '
   'where Bootstrap owns the geometry - the category Show-ButtonDrift '
   'excludes by name', btn_where)"""

GW_COUNT_WAS = r"""btn = 0
for rel, p in templates():
    if rel == 'base.html':
        continue
    btn += len(re.findall(r'\bbtn-(?:outline-)?(?:success|warning)\b',
                          read(p)))"""
GW_COUNT_NOW = r"""# COMMENTS OUT FIRST. Reading the raw file counted four
# - the three real ones and the words btn-success inside a comment that
# exists to say there is no btn-success on that page. A census of code
# that reads prose counts prose.
btn, btn_where = 0, {}
for rel, p in templates():
    if rel == 'base.html':
        continue
    _bare = re.sub(r'<!--.*?-->|/\*.*?\*/', '', read(p), flags=re.S)
    _n = len(re.findall(r'\bbtn-(?:outline-)?(?:success|warning)\b', _bare))
    if _n:
        btn_where[rel] = _n
        btn += _n"""

q = os.path.join(os.getcwd(), GW)
if os.path.isfile(q):
    tg, rawg = read(q)
    print('  %s' % GW)
    if 'btn_where' in tg:
        print('     already counts three, by name')
    else:
        for was, now, what in ((GW_COUNT_WAS, GW_COUNT_NOW,
                                'its census strips comments first'),
                               (GW_WAS, GW_NOW,
                                '  and the floor is three, named rather '
                                'than counted')):
            a = eol(q, was)
            if tg.count(a) != 1:
                raise SystemExit('R1: %s - an anchor matched %d time(s), '
                                 'not 1' % (GW, tg.count(a)))
            tg = tg.replace(a, eol(q, now), 1)
            print('     %s' % what)
        if not CHECK:
            back_up(q, rawg)
            write(q, tg)

# ---- THE TREE-WIDE GATE -------------------------------------------------
if not CHECK:
    left = {}
    for p in alv_tree.templates():
        rel = alv_tree.rel(p)
        if rel == 'base.html':
            continue
        hits = FAM.findall(nocom(read(p)[0]))
        if hits:
            left[rel] = len(hits)
    if sorted(left) != [LEFT]:
        raise SystemExit('R1: a Bootstrap tone survives on %s' % left)

print('-' * 74)
print('  %d controls take the weight their consequence deserves, and the'
      % moved)
print('  only green left in the system is three buttons inside an input.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
