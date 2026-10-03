# -*- coding: utf-8 -*-
"""MC-2 - THE CALENDAR'S ROW ACTIONS BECOME THE ROW ACTIONS

Demetri, 3 Oct 2026: "On Calendar view, we have a lot of changes to do to
the colours to bring them in line."

The loudest of them is the week header. Five buttons, five filled
colours:

    View       #007bff   blue
    Edit       #ffc107   yellow, with black ink
    List       #28a745   green
    Duplicate  #0e7c8b   teal
    Delete     #dc3545   red

and inside each day card, a blue filled View and a red outlined x.

==========================================================================
THIS IS THE SAME FIVE ACTIONS ML-1 ALREADY CONVERTED
==========================================================================
ML-1 did this exact work on meal_plans.html on 2 Oct, one day ago, and
its note reads:

    "Five filled buttons in five colours became base's row-action strip:
     the same five actions, the same order, on .icon-action-btn. The
     page's own btn-view / btn-edit / btn-shopping / btn-duplicate /
     btn-delete rules and their ten literal colours went with them."

The Calendar page is the SAME MEAL PLAN with the SAME FIVE ACTIONS in
the SAME ORDER, and it kept a second, private copy of the control. Asked
whether to convert it or merely retone it, Demetri chose "the same icon
row as the List page", which is the only answer that leaves one control
in the tree instead of two.

So this round does not invent anything. It deletes the second copy.

==========================================================================
THE ICON FOR EDIT CHANGES, DELIBERATELY
==========================================================================
The Calendar page drew Edit with fa-edit; the list rows draw it with
fa-pencil-alt. Two icons for one verb on two views of one object is the
same defect as two stylesheets for one control, so the calendar takes the
list page's icon. Named here because a silent icon change is the kind of
thing that gets found six weeks later and cannot be explained.

==========================================================================
AND THE x BECOMES A TRASHCAN
==========================================================================
The recipe card's remove control was a red-outlined x. Every other
destructive control in the tree is .icon-delete with fa-trash, and a
lone x is the only place a reader has to learn a second vocabulary for
"this removes something". It becomes the trashcan. The ACTION is
unchanged - removeRecipe() with the same two arguments - only the
costume.

==========================================================================
WHAT GOES, NAMED SO THE REMOVAL IS ALLOWED
==========================================================================
  .week-detail-actions and its two .btn rules (there were two, 470 lines
  apart, one setting 8px 16px and the other 8px 14px - the later one won
  and the earlier one had been dead for as long as both existed)
  .btn-view .btn-edit .btn-shopping .btn-duplicate .btn-delete and their
  five hovers - ten declarations, nine literal colours
  .btn-action-disabled
  .recipe-actions and its .btn rule
  the two 768px fragments that sized a control that no longer exists

Twelve literals leave with them: #007bff #0056b3 #ffc107 #e0a800 #000
(twice) #28a745 #218838 #0e7c8b #dc3545 #c82333 #6c757d.

Backups: .bak_calactions. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_calactions'
ROOT = os.getcwd()
CRLF = {}
CAL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_calendar.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('MC2: %s is not a byte copy' % bak)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


def swap(text, old, new, what, path=CAL):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('MC2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('MC-2 - THE CALENDAR ROW ACTIONS BECOME ICON BUTTONS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(CAL)
BEFORE = code_only(t.replace('\r\n', '\n'))

# --------------------------------------------------------------------------
# 0. THE PREMISE. Two .week-detail-actions .btn rules, 470 lines apart.
# --------------------------------------------------------------------------
n_rule = len(re.findall(r'\.week-detail-actions \.btn \{', BEFORE))
if 'icon-action-btn' not in BEFORE and n_rule != 2:
    raise SystemExit('MC2: expected two .week-detail-actions .btn rules, '
                     'found %d - the page is not what this round read'
                     % n_rule)

if 'icon-action-btn' in BEFORE:
    print('  meal_plan_calendar.html    already on the row-action strip')
else:
    print('  the page carries %d .week-detail-actions .btn rules, 470 lines '
          'apart' % n_rule)

    # ======================================================================
    # 1. THE WEEK HEADER - five buttons become the five icons.
    # ======================================================================
    t = swap(t, """            <div class="week-detail-actions">
                <a href="{% url 'view_meal_plan' selected_meal_plan.meal_plan_id %}" class="btn btn-view">
                    <i class="fas fa-eye"></i> View
                </a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_meal_plan' selected_meal_plan.meal_plan_id %}" class="btn btn-edit">
                    <i class="fas fa-edit"></i> Edit
                </a>
                {% else %}
                <span class="btn btn-action-disabled" title="No permission to edit">
                    <i class="fas fa-edit"></i> Edit
                </span>
                {% endif %}
                <a href="{% url 'meal_plan_shopping_list' selected_meal_plan.meal_plan_id %}" class="btn btn-shopping">
                    <i class="fas fa-shopping-cart"></i> List
                </a>
                {% if perms.auth.can_edit_personal %}
                <button type="button" class="btn btn-duplicate"
                        onclick="confirmDuplicate('{% url 'duplicate_meal_plan' selected_meal_plan.meal_plan_id %}', '{{ selected_meal_plan.plan_name|escapejs }}')">
                    <i class="fas fa-copy"></i> Duplicate
                </button>
                <button type="button" class="btn btn-delete"
                        onclick="confirmDelete('{% url 'delete_meal_plan' selected_meal_plan.meal_plan_id %}', '{{ selected_meal_plan.plan_name|escapejs }}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
                {% else %}
                <span class="btn btn-action-disabled" title="No permission to duplicate">
                    <i class="fas fa-copy"></i> Duplicate
                </span>
                <span class="btn btn-action-disabled" title="No permission to delete">
                    <i class="fas fa-trash"></i> Delete
                </span>
                {% endif %}
            </div>""",
             """            {# MC-2, 3 Oct 2026. The same five actions the list rows      #}
            {# already wear, in the same order, on base's .row-actions.    #}
            {# ML-1 converted the list page one day earlier; this page was #}
            {# a second private copy of the same control in five filled    #}
            {# colours. Edit takes the list page's fa-pencil-alt, not this #}
            {# page's fa-edit - two icons for one verb on two views of one #}
            {# object is the same defect as two stylesheets for one        #}
            {# control, only harder to see.                                #}
            {#                                                             #}
            {# EVERY ICON CARRIES A LABEL. An icon-only button is nothing  #}
            {# at all to a screen reader, and title= is not a substitute - #}
            {# it is a tooltip, read by some assistive tech and not by     #}
            {# others.                                                     #}
            <div class="row-actions">
                <a href="{% url 'view_meal_plan' selected_meal_plan.meal_plan_id %}"
                   class="icon-action-btn icon-view" title="View"
                   aria-label="View this meal plan"><i class="fas fa-eye"></i></a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_meal_plan' selected_meal_plan.meal_plan_id %}"
                   class="icon-action-btn icon-edit" title="Edit"
                   aria-label="Edit this meal plan"><i class="fas fa-pencil-alt"></i></a>
                {% else %}
                <span class="icon-action-btn icon-disabled" title="No permission to edit"
                      aria-label="Edit this meal plan, no permission"><i class="fas fa-pencil-alt"></i></span>
                {% endif %}
                <a href="{% url 'meal_plan_shopping_list' selected_meal_plan.meal_plan_id %}"
                   class="icon-action-btn icon-list" title="Shopping List"
                   aria-label="Shopping list for this meal plan"><i class="fas fa-shopping-cart"></i></a>
                {% if perms.auth.can_edit_personal %}
                <button type="button" class="icon-action-btn icon-duplicate" title="Duplicate"
                        aria-label="Duplicate this meal plan"
                        onclick="confirmDuplicate('{% url 'duplicate_meal_plan' selected_meal_plan.meal_plan_id %}', '{{ selected_meal_plan.plan_name|escapejs }}')"><i class="fas fa-copy"></i></button>
                <button type="button" class="icon-action-btn icon-delete" title="Delete"
                        aria-label="Delete this meal plan"
                        onclick="confirmDelete('{% url 'delete_meal_plan' selected_meal_plan.meal_plan_id %}', '{{ selected_meal_plan.plan_name|escapejs }}')"><i class="fas fa-trash"></i></button>
                {% else %}
                <span class="icon-action-btn icon-disabled" title="No permission to duplicate"
                      aria-label="Duplicate this meal plan, no permission"><i class="fas fa-copy"></i></span>
                <span class="icon-action-btn icon-disabled" title="No permission to delete"
                      aria-label="Delete this meal plan, no permission"><i class="fas fa-trash"></i></span>
                {% endif %}
            </div>""",
             'the week header actions')

    # ======================================================================
    # 2. THE RECIPE CARDS - blue View and a red x become two icons.
    # ======================================================================
    t = swap(t, """                                        <div class="recipe-actions">
                                            <a href="{% url 'view_recipe' recipe.recipe_id %}" class="btn btn-primary btn-sm">
                                                <i class="fas fa-eye"></i> View
                                            </a>
                                            {% if perms.auth.can_edit_personal %}
                                            <button class="btn btn-outline-danger btn-sm"
                                                    onclick="removeRecipe({{ recipe.meal_plan_recipe_id }}, '{{ recipe.name|escapejs }}')">
                                                <i class="fas fa-times"></i>
                                            </button>
                                            {% else %}
                                            <span class="btn btn-action-disabled btn-sm" title="No permission to remove">
                                                <i class="fas fa-times"></i>
                                            </span>
                                            {% endif %}
                                        </div>""",
             """                                        {# MC-2. And the x becomes a trashcan. Every other      #}
                                        {# destructive control in the tree is .icon-delete with #}
                                        {# fa-trash; a lone x was the only place a reader had   #}
                                        {# to learn a second word for "this removes something". #}
                                        {# removeRecipe() is called with the same two arguments #}
                                        {# as before - only the costume changed.                #}
                                        <div class="row-actions">
                                            <a href="{% url 'view_recipe' recipe.recipe_id %}"
                                               class="icon-action-btn icon-view" title="View recipe"
                                               aria-label="View the recipe {{ recipe.name }}"><i class="fas fa-eye"></i></a>
                                            {% if perms.auth.can_edit_personal %}
                                            <button type="button" class="icon-action-btn icon-delete"
                                                    title="Remove from this day"
                                                    aria-label="Remove {{ recipe.name }} from this day"
                                                    onclick="removeRecipe({{ recipe.meal_plan_recipe_id }}, '{{ recipe.name|escapejs }}')"><i class="fas fa-trash"></i></button>
                                            {% else %}
                                            <span class="icon-action-btn icon-disabled" title="No permission to remove"
                                                  aria-label="Remove this recipe, no permission"><i class="fas fa-trash"></i></span>
                                            {% endif %}
                                        </div>""",
             'the recipe card actions')

    # ======================================================================
    # 3. THE CSS THE TWO STRIPS CARRIED.
    # ======================================================================
    t = swap(t, """.week-detail-actions {
    display: flex;
    gap: 10px;
}

.week-detail-actions .btn {
    padding: 8px 16px;
    font-size: 13px;
    border-radius: 6px;
}""",
             """/* ROW ACTIONS - MC-2, 3 Oct 2026. .week-detail-actions is gone and so
   are both of its .btn rules. There were TWO, 470 lines apart, one
   setting 8px 16px and the other 8px 14px; the later one won and the
   earlier one had been dead for as long as both existed. The strip is
   base's .row-actions now, which is what the list rows have worn since
   ML-1. */""",
             'the week-detail-actions flex rules')

    t = swap(t, """.recipe-actions {
    display: flex;
    gap: 6px;
}

.recipe-actions .btn {
    padding: 4px 10px;
    font-size: 11px;
    border-radius: 4px;
}""",
             """/* .recipe-actions went the same way - MC-2. Base sizes .row-actions and
   .icon-action-btn, including the 44px touch target under 768px, so a
   page rule here could only disagree with it. */""",
             'the recipe-actions rules')

    t = swap(t, """/* Action Button Styles */
.week-detail-actions .btn {
    padding: 8px 14px;
    font-size: 12px;
    border-radius: 5px;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: none;
    text-decoration: none;
}

.btn-view {
    background: #007bff;
    color: white;
}

.btn-view:hover {
    background: #0056b3;
    color: white;
}

.btn-edit {
    background: #ffc107;
    color: #000;
}

.btn-edit:hover {
    background: #e0a800;
    color: #000;
}

.btn-shopping {
    background: #28a745;
    color: white;
}

.btn-shopping:hover {
    background: #218838;
    color: white;
}

.btn-duplicate {
    background: #0e7c8b;
    color: white;
    cursor: pointer;
}

.btn-duplicate:hover {
    background: var(--alv-accent-ink);
    color: white;
}

.btn-delete {
    background: #dc3545;
    color: white;
    cursor: pointer;
}

.btn-delete:hover {
    background: #c82333;
    color: white;
}

.btn-action-disabled {
    background: var(--alv-surface-deep) !important;
    color: #6c757d !important;
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
}""",
             """/* THE FIVE COLOURS - MC-2, 3 Oct 2026, and the reason this round
   exists. .btn-view #007bff, .btn-edit #ffc107 on black ink,
   .btn-shopping #28a745, .btn-duplicate #0e7c8b, .btn-delete #dc3545,
   their five hovers and .btn-action-disabled are all gone. Twelve
   literals left with them.

   Five filled colours in one row is not a palette, it is five
   independent decisions sitting next to each other, and it taught the
   reader nothing: the colour of Edit said "Edit" and nothing else. The
   row-action strip says the same five things in one quiet voice and
   keeps red for the one action that cannot be undone.

   Disabled is base's .icon-disabled now rather than a local
   !important pair. */""",
             'the five colour rules')

    # ======================================================================
    # 4. AND THE 768 FRAGMENTS THAT SIZED THEM.
    # ======================================================================
    t = swap(t, """    /* Week detail actions — 5 buttons in 3-col grid (3+2) */
    .week-detail-actions {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        width: 100%;
    }
    .week-detail-actions .btn,
    .week-detail-actions span.btn-action-disabled {
        padding: 9px 4px !important;
        font-size: 12px !important;
        justify-content: center;
        text-align: center;
        white-space: nowrap;
    }

""",
             """    /* The 3-col grid that wrapped five labelled buttons on a phone went
       with them - MC-2. Five icon buttons are five 44px targets, about
       250px of the 390px a phone gives, so they sit on one row and need
       no grid at all. */

""",
             'the week actions 768 fragment')

    t = swap(t, """    .recipe-actions .btn,
    .recipe-actions .btn-action-disabled {
        padding: 5px 9px;
        font-size: 11px;
    }
""", '', 'the recipe actions 768 fragment')

    if not CHECK:
        back_up(CAL, raw)
        write(CAL, t)
    print('  meal_plan_calendar.html    two strips converted, 10 rules and '
          '12 literals gone')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import alv_tree

NOW = code_only(read(CAL)[0].replace('\r\n', '\n'))
WAS = code_only(read(CAL + SUFFIX)[0].replace('\r\n', '\n'))
BASE = code_only(open(alv_tree.path_of('base.html'),
                      encoding='utf-8', errors='replace').read())

# 1. TWO STRIPS, AND BOTH OF THEM ARE base's.
n = NOW.count('class="row-actions"')
if n != 2:
    raise SystemExit('MC2: %d row-action strips, expected two' % n)
print('  two .row-actions strips - the week header and the recipe card')

# 2. THE SEVEN CONTROLS, BY NAME.
WANT = {'icon-view': 2, 'icon-edit': 1, 'icon-list': 1,
        'icon-duplicate': 1, 'icon-delete': 2, 'icon-disabled': 4}
for cls, k in sorted(WANT.items()):
    got = len(re.findall(r'\bicon-action-btn [a-z-]*\b%s\b' % cls, NOW))
    if got != k:
        raise SystemExit('MC2: %d .%s, expected %d' % (got, cls, k))
print('  %s' % ', '.join('%d %s' % (v, k) for k, v in sorted(WANT.items())))

# 3. EVERY ICON CARRIES A LABEL. An icon-only control with no label is
#    nothing at all to a screen reader, and this round made eleven of them.
btns = re.findall(r'<(?:a|button|span)[^>]*icon-action-btn[^>]*>', NOW)
bare = [b for b in btns if 'aria-label' not in b]
if bare:
    raise SystemExit('MC2: %d icon controls with no aria-label:\n   %s'
                     % (len(bare), '\n   '.join(b[:90] for b in bare[:4])))
print('  all %d icon controls carry an aria-label' % len(btns))

# 4. THE OLD NAMES ARE GONE - markup AND rules.
for dead in ('week-detail-actions', 'recipe-actions', 'btn-view', 'btn-edit',
             'btn-shopping', 'btn-duplicate', 'btn-delete',
             'btn-action-disabled', 'btn-outline-danger'):
    if re.search(r'\b%s\b' % dead, NOW):
        raise SystemExit('MC2: %s is still in the code' % dead)
print('  none of the nine old names survive in code')

# 5. THE TWELVE LITERALS, COUNTED AGAINST THE BACKUP. Not asserted
#    absolute - #28a745 is on the left panel's Create button too, and
#    #6c757d is on four other rules. A gate that claimed the page was
#    clean of them would be claiming MC-3's work as well as its own.
DROP = {'#007bff': 1, '#0056b3': 1, '#ffc107': 1, '#e0a800': 1,
        '#000;': 2, '#218838': 1, '#0e7c8b': 1, '#c82333': 1}
for lit, k in sorted(DROP.items()):
    got = WAS.count(lit) - NOW.count(lit)
    if got != k:
        raise SystemExit('MC2: dropped %d uses of %s, expected %d '
                         '(%d before, %d after)'
                         % (got, lit, k, WAS.count(lit), NOW.count(lit)))
print('  dropped %s' % ', '.join(sorted(DROP)))

# 6. AND THE TWO SHARED LITERALS, EACH MEASURED FOR WHAT IT ACTUALLY IS.
#
#    The first draft asserted that #dc3545 dropped one use and kept one,
#    by symmetry with #28a745. It had only ever had ONE use, on
#    .btn-delete, and this round took it - so the gate failed a correct
#    page by assuming two colours behave alike because they appear in the
#    same strip. Eleventh time this week. Each is now measured.
if WAS.count('#dc3545') != 1 or NOW.count('#dc3545') != 0:
    raise SystemExit('MC2: #dc3545 was %d uses and is now %d; this round '
                     'owns its only one, on .btn-delete'
                     % (WAS.count('#dc3545'), NOW.count('#dc3545')))
if WAS.count('#28a745') - NOW.count('#28a745') != 1 or NOW.count('#28a745') < 1:
    raise SystemExit('MC2: #28a745 went %d -> %d; this round owns exactly '
                     'one of its uses, on .btn-shopping, and MC-3 owns the '
                     'rest' % (WAS.count('#28a745'), NOW.count('#28a745')))
print('  #dc3545 had one use and this round took it; #28a745 had %d, this '
      'round took one, MC-3 owns the other %d'
      % (WAS.count('#28a745'), NOW.count('#28a745')))

# 7. BASE REALLY DEFINES WHAT THE PAGE NOW ASKS FOR.
for cls in ('.row-actions', '.icon-action-btn', '.icon-view', '.icon-edit',
            '.icon-list', '.icon-duplicate', '.icon-delete',
            '.icon-action-btn.icon-disabled'):
    if not re.search(re.escape(cls) + r'[\s,{:]', BASE):
        raise SystemExit('MC2: base does not define %s' % cls)
print('  base defines all eight classes the page now asks for')

# 8. THE CONTROL: the page really did carry two .btn rules for one strip,
#    470 lines apart. If it did not, the premise of section 0 is wrong.
pos = [m.start() for m in re.finditer(r'\.week-detail-actions \.btn \{', WAS)]
if len(pos) != 2:
    raise SystemExit('MC2: the page had %d such rules, not two' % len(pos))
gap = WAS.count('\n', pos[0], pos[1])
print('  CONTROL: the page really did carry two rules for one strip, %d '
      'lines apart' % gap)

# 9. THE ACTIONS THEMSELVES DID NOT MOVE. A costume change that quietly
#    changed what a button DOES is the thing this gate exists to refuse.
for call in ("confirmDuplicate('{% url 'duplicate_meal_plan'",
             "confirmDelete('{% url 'delete_meal_plan'",
             "removeRecipe({{ recipe.meal_plan_recipe_id }}, "
             "'{{ recipe.name|escapejs }}')"):
    if NOW.count(call) != WAS.count(call) or NOW.count(call) == 0:
        raise SystemExit('MC2: the call %r changed (%d before, %d after)'
                         % (call[:40], WAS.count(call), NOW.count(call)))
for url in ('view_meal_plan', 'edit_meal_plan', 'meal_plan_shopping_list',
            'duplicate_meal_plan', 'delete_meal_plan', 'view_recipe'):
    if NOW.count("{%% url '%s'" % url) != WAS.count("{%% url '%s'" % url):
        raise SystemExit('MC2: the %s link count changed' % url)
print('  every handler and every url resolves to the same thing it did')

print('-' * 74)
print('  One control, not two. ML-1 did this to the list rows a day ago;')
print('  the Calendar page was the second private copy, and five filled')
print('  colours in one row were five decisions that taught nobody')
print('  anything - the colour of Edit only ever said "Edit".')
print('=' * 74)
