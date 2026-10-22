# -*- coding: utf-8 -*-
"""apply_day_order.py - round RO-1, 21 Oct 2026.

THE DAY CARD HAD NO WAY TO SAY WHAT COMES FIRST.

Demetri, 21 October:

    "For the reordering, do we need the buttons. Can we not just have
     like three lines or something that somebody clicks on and then
     drags and drops (similar to Ingredients and Instructions
     entry)???"

SO IT IS THE HANDLE THIS APPLICATION ALREADY HAS. preview_imported_recipe
has dragged ingredients and instructions with SortableJS 1.15.0 since it
was written: a `.drag-handle` carrying `fa-grip-vertical`, with `handle`,
`ghostClass`, `dragClass`, `chosenClass` and `animation: 150`. This round
uses those names and that version, read off that page rather than typed
here. A second drag idiom on the same screens would be a second thing to
learn.

WHAT IT NEEDED THAT DID NOT EXIST. sort_order has decided the order of a
day since MN-1 and nothing in the application could write it: every
endpoint that makes a row puts it at the TAIL. So there is a new view,
reorder_meal_day, and it is the only thing in the system that moves a
row within its day.

IT REFUSES RATHER THAN GUESSES. The order that arrives must be exactly
the set of rows on that date - none missing, none added, none twice. A
page left open while somebody else cooked would otherwise write an order
that silently drops whatever it never knew about. On a mismatch it
answers 409 with the real order and the page puts itself right.

THE HANDLE IS NOT DRAWN UNTIL THE LIBRARY ANSWERS. The script comes from
a CDN and a CDN can fail. A grip you can press that does nothing is
worse than no grip, so `.drag-handle` is hidden by default and the row
list only gains `is-draggable` once `Sortable` is really there. With it
missing the card is exactly what it was this morning, Move included.

THE BUTTONS STAY. RD-2 put Move-to-another-day on this card on 19
October and it answers a different question: dragging says what comes
first ON this day, Move says WHICH day. Removing one because the other
arrived would be the second-way-to-do-the-same-thing fault in reverse.

THE ROWS NEEDED A WRAPPER. .day-card-body holds the rows AND the Add
Recipe / Add Note row, so a sortable bound to it would let a meal be
dropped below the buttons. The rows now sit in .day-rows, which carries
the date, and that is what is sortable.

Idempotent. Every file backed up to .bak_dayorder.
"""
import os
import re
import sys

SUFFIX = '.bak_dayorder'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
PREVIEW = os.path.join('pages', 'templates', 'preview_imported_recipe.html')
GUIDE = os.path.join('pages', 'help_content', 'administration.html')
G5 = 'test_meal_guide5.py'
G3 = 'test_meal_guide3.py'
MH = 'test_meal_help.py'
ME = 'test_day_order.py'
PATCHER = 'apply_day_order.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RO-1, 21 Oct 2026'
CHECK = False
CREATES = ()
SORTABLE = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js'

# ==========================================================================
# THE VIEW
# ==========================================================================
VIEW_WAS = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_meal_entry(request):"""

VIEW_NOW = '''@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def reorder_meal_day(request):
    """Write the order a drag left a day in. RO-1, 21 Oct 2026.

    Demetri, 21 October:

        "For the reordering, do we need the buttons. Can we not just
         have like three lines or something that somebody clicks on
         and then drags and drops (similar to Ingredients and
         Instructions entry)???"

    THE COLUMN WAS ALWAYS THERE AND NOTHING COULD WRITE IT. sort_order
    has decided the order of a day since MN-1; every endpoint that
    makes a row puts it at the TAIL and no endpoint ever moved one.
    This is that endpoint, and it is the only one.

    IT REFUSES RATHER THAN GUESSES. What arrives must be exactly the
    set of rows on that date - none missing, none added, none twice. A
    page left open while somebody else cooked would otherwise write an
    order that quietly drops whatever it never knew about. On a
    mismatch this answers 409 WITH THE REAL ORDER, so the page can put
    itself right instead of guessing too.

    ONE UPDATE PER ROW, inside a transaction. A day holds a handful of
    meals; bulk_update for five rows would be cleverness with no
    reader.

    A LEFTOVER DRAGS LIKE ANYTHING ELSE. It is tied to the meal it
    came from by leftover_of and not by position, so moving it up the
    day changes what you read first and nothing else.
    """
    day = week_of(request.POST.get('date'), None)
    if day is None:
        return JsonResponse({'ok': False, 'why': 'date'}, status=400)

    raw = (request.POST.get('order') or '').strip()
    try:
        ids = [int(x) for x in raw.split(',') if x.strip() != '']
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'why': 'order'}, status=400)
    if not ids:
        return JsonResponse({'ok': False, 'why': 'empty'}, status=400)
    if len(set(ids)) != len(ids):
        return JsonResponse({'ok': False, 'why': 'twice'}, status=400)

    on_day = list(MealEntry.objects.filter(date=day)
                  .order_by('sort_order', 'meal_entry_id')
                  .values_list('meal_entry_id', flat=True))
    if set(ids) != set(on_day):
        return JsonResponse({'ok': False, 'why': 'stale',
                             'order': on_day}, status=409)

    with transaction.atomic():
        for n, eid in enumerate(ids, start=1):
            MealEntry.objects.filter(meal_entry_id=eid).update(sort_order=n)

    return JsonResponse({'ok': True, 'order': ids})


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_meal_entry(request):'''

INDEX_WAS = """- remove_meal_entry               : Take one off (POST). Edit-tier."""

INDEX_NOW = """- remove_meal_entry               : Take one off (POST). Edit-tier.
- reorder_meal_day                : What comes first on a day (POST,
                                    JSON). Edit-tier. The only endpoint
                                    that moves a row WITHIN its date -
                                    every other one appends. It refuses
                                    an order that is not exactly the
                                    rows on that date.
                                    RO-1, 21 Oct 2026."""

URL_WAS = """    # PS-1, 19 Oct 2026 - what is on one day, for the picker's strip.
    path('meal_plans/day_entries/', views.meal_day_entries,
         name='meal_day_entries'),"""

URL_NOW = """    # RO-1, 21 Oct 2026 - what comes first on a day. Beside move,
    # because the two are halves of where a meal sits: move says which
    # day, this says where on it.
    path('meal_plans/reorder/', views.reorder_meal_day,
         name='reorder_meal_day'),
    # PS-1, 19 Oct 2026 - what is on one day, for the picker's strip.
    path('meal_plans/day_entries/', views.meal_day_entries,
         name='meal_day_entries'),"""

# ==========================================================================
# THE MARKUP - a wrapper the rows live in, and a grip on each one
# ==========================================================================
ROWS_OPEN_WAS = """                    <div class="day-card-body">
                        {% for entry in day.entries %}"""

ROWS_OPEN_NOW = """                    <div class="day-card-body">
                        {# .day-rows - RO-1, 21 Oct 2026.                    #}
                        {#                                                   #}
                        {# THE ROWS NEEDED SOMETHING OF THEIR OWN TO LIVE IN.#}
                        {# .day-card-body holds these rows AND the Add       #}
                        {# Recipe / Add Note row below them, so a sortable   #}
                        {# bound to the body would let a meal be dropped     #}
                        {# underneath the buttons.                           #}
                        {#                                                   #}
                        {# The date rides on the wrapper because the endpoint#}
                        {# asks for it: an order is only meaningful about a  #}
                        {# particular day.                                   #}
                        <div class="day-rows" data-day="{{ day.date|date:'Y-m-d' }}">
                        {% for entry in day.entries %}"""

ROWS_CLOSE_WAS = """                        <div class="empty-day">
                            <i class="fas fa-utensils"></i>
                            <p>Nothing planned</p>
                        </div>
                        {% endfor %}

                        {# EVERY DATE CAN TAKE A MEAL."""

ROWS_CLOSE_NOW = """                        <div class="empty-day">
                            <i class="fas fa-utensils"></i>
                            <p>Nothing planned</p>
                        </div>
                        {% endfor %}
                        </div>{# .day-rows - RO-1, 21 Oct 2026 #}

                        {# EVERY DATE CAN TAKE A MEAL."""

GRIP = """                            {# THE GRIP - RO-1, 21 Oct 2026. The same handle  #}
                            {# preview_imported_recipe has dragged ingredients #}
                            {# and instructions with since it was written.     #}
                            {# HIDDEN until Sortable answers: a grip you can   #}
                            {# press that does nothing is worse than no grip.  #}
                            <span class="drag-handle" aria-hidden="true"
                                  title="Drag to reorder this day"><i class="fas fa-grip-vertical"></i></span>
"""

LEFTOVER_WAS = """                        <div class="recipe-item leftover-item" data-entry="{{ entry.meal_entry_id }}">
                            {% if entry.recipe.photo_url %}"""

MEAL_WAS = """                        <div class="recipe-item" data-entry="{{ entry.meal_entry_id }}">
                            {% if entry.recipe.photo_url %}"""

NOTE_WAS = """                        <div class="recipe-item note-item" data-entry="{{ entry.meal_entry_id }}">
                            <div class="recipe-thumbnail-placeholder">"""

# ==========================================================================
# THE RULES
# ==========================================================================
CSS_WAS = """/* THE MENUS DIALOG - two sections, two forms, one dialog. */"""

CSS_NOW = """/* DRAGGING A DAY INTO ORDER - RO-1, 21 Oct 2026.

   THE GRIP IS HIDDEN UNTIL THE LIBRARY ANSWERS. Sortable comes from a
   CDN; a CDN can fail, and a handle you can press that does nothing is
   worse than no handle. The script adds .is-draggable to the list only
   once `Sortable` is really there, so a failed load leaves the card
   exactly as it was.

   THE NAMES ARE preview_imported_recipe's. That page has dragged
   ingredients and instructions since it was written - .drag-handle,
   .sortable-ghost, .sortable-drag, .sortable-chosen - and a second
   vocabulary for the same gesture would be a second thing to learn. */
.day-rows .drag-handle { display: none; }
.day-rows.is-draggable .drag-handle {
    display: flex;
    align-items: center;
    align-self: stretch;
    padding: 6px 8px;
    margin-right: 2px;
    color: var(--alv-ink-faint);
    cursor: grab;
    touch-action: none;
}
.day-rows.is-draggable .drag-handle:hover { color: var(--alv-ink-soft); }
.day-rows.is-draggable .drag-handle:active { cursor: grabbing; }
.day-rows .sortable-ghost { opacity: 0.4; }
.day-rows .sortable-drag { opacity: 0.9; }
.day-rows .sortable-chosen { background: var(--alv-surface); }
/* THE PHONE RULES FOR THESE ARE IN THE PAGE'S OWN PHONE BLOCK, further
   down, and NOT in a new one here. Opening a second
   `@media screen and (max-width: 768px)` above the first one moved
   where the first one STARTS, and three suites slice this stylesheet
   on exactly that string to find "the phone block" - test_meal_week
   says so in as many words: "A scope that silently lands on the wrong
   block is the same fault as a fallback that silently widens one."
   It landed on the wrong block, and the sweep caught it. */

/* THE MENUS DIALOG - two sections, two forms, one dialog. */"""

# ==========================================================================
# THE SCRIPT
# ==========================================================================
JS_WAS = """function removeMeal(entryId, name) {
    if (!confirm('Remove "' + name + '" from this day?')) { return; }
    document.getElementById('removeEntryId').value = entryId;
    document.getElementById('removeForm').submit();
}"""

JS_NOW = """function removeMeal(entryId, name) {
    if (!confirm('Remove "' + name + '" from this day?')) { return; }
    document.getElementById('removeEntryId').value = entryId;
    document.getElementById('removeForm').submit();
}

// ------------------------------------------------- dragging a day
// RO-1, 21 Oct 2026.
//
//     "Can we not just have like three lines or something that
//      somebody clicks on and then drags and drops (similar to
//      Ingredients and Instructions entry)???"
//
// SO IT IS THE SAME LIBRARY AND THE SAME OPTIONS preview_imported_recipe
// uses. handle, ghostClass, dragClass, chosenClass, animation 150.
//
// NOTHING IS DRAWN UNTIL Sortable ANSWERS. The guard is the whole
// degradation story: no library, no .is-draggable, no grip, and the
// card is what it was before this round. RL-1's lesson from 20 October
// is in here too - this runs at the END of the document, where the
// CDN tag above it has already resolved or failed.
(function () {
    if (typeof Sortable === 'undefined') { return; }
    var list = document.querySelector('.day-rows');
    if (!list || !list.querySelector('.drag-handle')) { return; }
    list.classList.add('is-draggable');
    new Sortable(list, {
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        dragClass: 'sortable-drag',
        chosenClass: 'sortable-chosen',
        animation: 150,
        onEnd: function () { saveDayOrder(list); }
    });
}());

// WHAT THE DROP SENDS. The ids in the order they now sit in, and the
// day they sit on - the endpoint will not take one without the other.
function saveDayOrder(list) {
    var ids = [].map.call(list.querySelectorAll('[data-entry]'),
        function (r) { return r.getAttribute('data-entry'); });
    if (!ids.length) { return; }
    var body = new FormData();
    body.append('date', list.getAttribute('data-day'));
    body.append('order', ids.join(','));
    body.append('csrfmiddlewaretoken', '{{ csrf_token }}');
    list.classList.add('is-saving');
    fetch('{% url "reorder_meal_day" %}', {
        method: 'POST', credentials: 'same-origin', body: body
    })
        .then(function (r) {
            // 409 MEANS THE DAY CHANGED UNDER US and the server sent
            // back what is really on it. Reloading is the honest
            // answer: this page is looking at something that is no
            // longer true, and guessing which rows it missed would be
            // the same mistake the endpoint refuses to make.
            if (r.status === 409) { window.location.reload(); return null; }
            if (!r.ok) { throw new Error(r.status); }
            return r.json();
        })
        .catch(function () {
            // A FAILED SAVE MUST NOT LEAVE A LIE ON THE SCREEN. The
            // rows are sitting in an order the database does not have.
            window.location.reload();
        })
        .then(function () { list.classList.remove('is-saving'); });
}"""

# THE PLANNER HAS NO extra_scripts BLOCK - its scripts are inline in
# the content block. So the library goes immediately above the script
# that uses it, which is also where a reader looking for it will be.
CDN_WAS = """<script>
// =====================================================================
// MN-1, 18 Oct 2026. The planner."""

CDN_NOW = """{# SORTABLE 1.15.0 - RO-1, 21 Oct 2026. The version and the URL are    #}
{# preview_imported_recipe's, so the browser has one copy to cache and #}
{# this project has one answer to which version it drags with.         #}
{#                                                                     #}
{# IF THIS FAILS TO LOAD THE DAY CARD LOSES NOTHING: the grip is hidden #}
{# until the guard at the foot of this page sees Sortable and says so.  #}
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script>
// =====================================================================
// MN-1, 18 Oct 2026. The planner."""

# ---- THE PHONE RULES, IN THE PAGE'S OWN PHONE BLOCK.
#
# NOT IN A NEW ONE. Three suites find "the phone block" by splitting
# this stylesheet on the FIRST `@media screen and (max-width: 768px)`,
# so a second one opened above it moves where the first begins and
# drags desktop rules into their slice. The first draft of this round
# did that and the sweep found it in test_meal_week, which had written
# the warning down: "A scope that silently lands on the wrong block is
# the same fault as a fallback that silently widens one."
PHONE_WAS = """@media screen and (max-width: 768px) {
    .calendar-container {
        padding: 8px;
    }"""

PHONE_NOW = """@media screen and (max-width: 768px) {
    /* DRAGGING, ON A PHONE - RO-1, 21 Oct 2026.
       22px and the padding make the grip a 44px target, which is the
       house floor for anything you press.

       AND THE ACTIONS WRAP, BECAUSE 44px HAD TO COME FROM SOMEWHERE.
       At 390px the row is 286px wide and .row-actions already wanted
       194 of a 183px share - eleven pixels over, which nobody could
       see. The grip takes 44 more and the fourth button went off the
       edge of the card. Measured in Chromium, not guessed: the
       before-and-after renders caught it.

       WRAPPING RATHER THAN SHRINKING. A narrower grip would buy the
       pixels by breaking the 44px floor, and dropping a button would
       be paying for a drag with a control that does something else.
       Scoped to .day-rows, so base's own .row-actions is untouched
       everywhere else in the system. */
    .day-rows.is-draggable .drag-handle { font-size: 22px; padding: 6px 8px; }
    .day-rows .row-actions { flex-wrap: wrap; row-gap: 6px; }

    .calendar-container {
        padding: 8px;
    }"""

# ==========================================================================
# THE HELP GUIDE, AND THE THREE SUITES THAT PIN IT
# ==========================================================================
# MH-3 WROTE A PROMISE AND THIS ROUND KEEPS IT. The Meal Plans guide has
# named "reordering the meals on a day" as the one thing not yet built
# since 19 October, and three suites pin that sentence: test_meal_guide5
# and test_meal_guide3 hold the string in an OUTSTANDING constant, and
# test_meal_help asks the rendered guide for it. test_meal_guide5 also
# carries a CONTROL asserting the view cannot reorder a day - which this
# round makes false, and deliberately.
#
# THE PROMISE MOVES RATHER THAN DISAPPEARING. The Week view's seven
# columns still cannot be dragged, that question was put to Demetri and
# is not yet answered, and this round explicitly does not do it. So the
# guide names THAT as outstanding and the three pins follow it. A guide
# with nothing left to promise would also have meant rewriting what
# each of those suites counts, for a sentence that is not true: there
# IS something left.
GUIDE_WAS = """      <i class="fas fa-info-circle"></i> <strong>Not yet, and coming:</strong> reordering the meals on a day. Moving one from day to day, which stood here beside it, is <strong>Move</strong> on the chip menu now."""

GUIDE_NOW = """      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use. <strong>Not yet, and coming:</strong> reordering the week view. Moving a meal from day to day, which stood here beside it, is <strong>Move</strong> on the chip menu now."""

G5_OUT_WAS = """# And the one that is not, which must still be named.
OUTSTANDING = 'reordering the meals on a day'"""

G5_OUT_NOW = """# And the one that is not, which must still be named.
# RO-1, 21 Oct 2026 - A DAY CAN BE DRAGGED INTO ORDER NOW, so the thing
# the guide names as outstanding moved on rather than disappearing: the
# WEEK view's seven columns still cannot be dragged, that question is
# with Demetri and unanswered, and RO-1 explicitly does not do it.
OUTSTANDING = 'reordering the week view'"""

G3_OUT_WAS = """OUTSTANDING = 'reordering the meals on a day'"""

G3_OUT_NOW = """# RO-1, 21 Oct 2026 - the day can be dragged now; the week cannot.
OUTSTANDING = 'reordering the week view'"""

G5_CTL_WAS = """ok('def reorder' not in view,
   'CONTROL: and there is still no way to reorder a day, so the one '"""

G5_CTL_NOW = """ok('def reorder_meal_day' in view and 'def reorder_week' not in view,
   'CONTROL: a DAY can be reordered now and a WEEK cannot, so the one '"""

G5_PIN_WAS = """    c['  and its outstanding pin moved to reordering'] = (
        "OUTSTANDING = 'reordering the meals on a day'" in g3)"""

G5_PIN_NOW = """    c['  and its outstanding pin moved to reordering'] = (
        "OUTSTANDING = 'reordering the week view'" in g3)"""

MH_WAS = """    ok(any('reordering the meals on a day' in s.lower()"""

MH_NOW = """    ok(any('reordering the week view' in s.lower()"""

# test_meal_help carries the SAME control as test_meal_guide5 - and for
# the same written reason: without it the guide's promise "would keep
# passing for as long as nobody edited the guide, however long after
# the feature shipped". That is exactly what this round is: the feature
# shipping. So the control moves to the thing that really is not built.
MH_CTL_WAS = """    ok('def reorder' not in view_py,
       '  CONTROL: and there is still no way to reorder a day')"""

MH_CTL_NOW = """    # RO-1, 21 Oct 2026 - A DAY REORDERS NOW. The reason this control
    # exists is untouched: a promise in a guide outlives the thing it
    # promised unless something asks the code. So it asks about the
    # WEEK, which is what the guide names now and what really is not
    # built.
    ok('def reorder_meal_day' in view_py
       and 'def reorder_week' not in view_py,
       '  CONTROL: a day reorders and a week does not, which is what '
       'the guide says')"""


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
    raise SystemExit('RO-1 REFUSED: %s' % msg)


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

    pv = os.path.join(root, VIEW)
    v = read(pv)

    if 'def reorder_meal_day' in v:
        print('RO-1  already applied - a day can be dragged into order.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE IDIOM IS READ OFF THE PAGE THAT ALREADY USES IT, not
    # typed here. If preview_imported_recipe ever changes library or
    # version, this round is the thing that would silently disagree.
    pp = os.path.join(root, PREVIEW)
    prev = read(pp)
    if SORTABLE not in prev:
        refuse('%s does not load %s - this round copies its idiom and '
               'cannot copy what is not there' % (PREVIEW, SORTABLE))
    for need in ("handle: '.drag-handle'", 'ghostClass', 'dragClass',
                 'chosenClass', 'fa-grip-vertical'):
        if need not in prev:
            refuse('%s no longer uses %s, so the handle this round adds '
                   'would be a second idiom' % (PREVIEW, need))

    # ---- THE COLUMN EXISTS AND NOTHING WRITES IT. That is the finding.
    vcode = T.python_code_only(v, payloads=True)
    if 'sort_order' not in vcode:
        refuse('%s: sort_order is gone' % VIEW)
    if 'def reorder' in vcode:
        refuse('%s: something already reorders a day' % VIEW)

    v = swap(v, INDEX_WAS, INDEX_NOW, '%s (the index)' % VIEW)
    v = swap(v, VIEW_WAS, VIEW_NOW, '%s (the view)' % VIEW)
    out[pv] = v

    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), URL_WAS, URL_NOW, '%s (the route)' % URLS)

    # ---- THE DAY CARD
    pt = os.path.join(root, TPL)
    t = read(pt)
    t = swap(t, ROWS_OPEN_WAS, ROWS_OPEN_NOW, '%s (the wrapper)' % TPL)
    t = swap(t, ROWS_CLOSE_WAS, ROWS_CLOSE_NOW, '%s (the close)' % TPL)
    # THE GRIP GOES ON ALL THREE ROW SHAPES. A day holds meals,
    # leftovers and notes, and an order with a hole in it is not an
    # order.
    for lit, what in ((LEFTOVER_WAS, 'leftover'), (MEAL_WAS, 'meal'),
                      (NOTE_WAS, 'note')):
        head = lit.split('\n')[0]
        t = swap(t, lit, head + '\n' + GRIP + '\n'.join(lit.split('\n')[1:]),
                 '%s (the %s grip)' % (TPL, what))
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the rules)' % TPL)
    t = swap(t, PHONE_WAS, PHONE_NOW, '%s (the phone block)' % TPL)
    t = swap(t, JS_WAS, JS_NOW, '%s (the script)' % TPL)
    t = swap(t, CDN_WAS, CDN_NOW, '%s (the library)' % TPL)
    out[pt] = t

    # ---- THE GUIDE, AND THE THREE SUITES THAT PIN IT
    ph = os.path.join(root, GUIDE)
    out[ph] = swap(read(ph), GUIDE_WAS, GUIDE_NOW, '%s (the promise)' % GUIDE)

    p5 = os.path.join(root, G5)
    g5 = read(p5)
    g5 = swap(g5, G5_OUT_WAS, G5_OUT_NOW, '%s (outstanding)' % G5)
    g5 = swap(g5, G5_CTL_WAS, G5_CTL_NOW, '%s (the control)' % G5)
    g5 = swap(g5, G5_PIN_WAS, G5_PIN_NOW, '%s (the pin)' % G5)
    out[p5] = g5

    p3 = os.path.join(root, G3)
    out[p3] = swap(read(p3), G3_OUT_WAS, G3_OUT_NOW, '%s (outstanding)' % G3)

    pm = os.path.join(root, MH)
    mh = read(pm)
    mh = swap(mh, MH_WAS, MH_NOW, '%s (the promise)' % MH)
    mh = swap(mh, MH_CTL_WAS, MH_CTL_NOW, '%s (the control)' % MH)
    out[pm] = mh

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_menu_range.py'
)""", """    'test_menu_range.py',
    # RO-1, 21 Oct 2026 - a day is dragged into order by its grip.
    'test_day_order.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'MENU_MAX_DAYS';""",
             """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def reorder_meal_day'; What = 'RO-1: the only endpoint that moves a row within its day - sort_order has decided the order since MN-1 and nothing could write it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'day-rows'; What = 'RO-1: the day card rows drag by the same grip the ingredients list uses, and the grip is hidden unless SortableJS actually loaded' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'MENU_MAX_DAYS';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # MN-2, 21 Oct 2026 - a menu is a span, and it lands where you say.
    'test_menu_range.py',
]""", """    # MN-2, 21 Oct 2026 - a menu is a span, and it lands where you say.
    'test_menu_range.py',
    # RO-1, 21 Oct 2026 - a day dragged into the order you want.
    'test_day_order.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # MN-2, 21 Oct 2026 - menus take a range.
    '.bak_menurange',
]""", """    # MN-2, 21 Oct 2026 - menus take a range.
    '.bak_menurange',
    # RO-1, 21 Oct 2026 - drag a day into order.
    '.bak_dayorder',
]""", '%s (ROUNDS)' % ROUNDS)

    pwd = os.path.join(root, WD)
    wd = read(pwd)
    n = re.search(r'CONVERTED_N = (\d+)', wd)
    out[pwd] = swap(wd, 'CONVERTED_N = %s' % n.group(1),
                    'CONVERTED_N = %d   # RO-1, 21 Oct 2026 - this round '
                    'own suite   # (was %s)'
                    % (int(n.group(1)) + 1, n.group(1)),
                    '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)
    rv = nv[nv.index('def reorder_meal_day'):nv.index('def remove_meal_entry')]
    # IT REFUSES RATHER THAN GUESSES, and the refusal carries the truth.
    if 'set(ids) != set(on_day)' not in rv:
        refuse('%s: the endpoint does not check the order against the day'
               % VIEW)
    if "status=409" not in rv or "'order': on_day" not in rv:
        refuse('%s: a stale order is not answered with the real one, so '
               'the page has nothing to put itself right with' % VIEW)
    if 'len(set(ids)) != len(ids)' not in rv:
        refuse('%s: the same row twice is not refused' % VIEW)
    if 'with transaction.atomic():' not in rv:
        refuse('%s: the renumber is not in a transaction' % VIEW)
    # AND IT IS EDIT-TIER, like everything else that writes.
    if "permission_required('auth.can_edit_recipes'" not in \
            out[pv][out[pv].index('def reorder_meal_day') - 220:
                    out[pv].index('def reorder_meal_day')]:
        refuse('%s: the endpoint is not edit-tier' % VIEW)
    if '@require_POST' not in \
            out[pv][out[pv].index('def reorder_meal_day') - 220:
                    out[pv].index('def reorder_meal_day')]:
        refuse('%s: the endpoint takes a GET' % VIEW)

    nt = out[pt]
    # THE GRIP IS ON EVERY ROW SHAPE AND NOWHERE ELSE ON THIS PAGE.
    if nt.count('class="drag-handle"') != 3:
        refuse('%s: %d grip(s), expected one on each of the three row '
               'shapes' % (TPL, nt.count('class="drag-handle"')))
    # AND IT IS HIDDEN UNTIL THE LIBRARY ANSWERS.
    css = T.code_only(nt)
    if '.day-rows .drag-handle { display: none; }' not in css:
        refuse('%s: the grip is drawn before Sortable has answered' % TPL)
    if '.day-rows.is-draggable .drag-handle' not in css:
        refuse('%s: nothing ever shows the grip' % TPL)
    js = T.code_only_js(nt)
    if "typeof Sortable === 'undefined'" not in js:
        refuse('%s: the script does not guard on the library being there'
               % TPL)
    if "classList.add('is-draggable')" not in js:
        refuse('%s: nothing adds the class that shows the grip' % TPL)
    # THE SORTABLE IS BOUND TO THE ROWS, NOT THE BODY.
    if "querySelector('.day-rows')" not in js:
        refuse('%s: the sortable is not bound to the row wrapper, so a '
               'meal could be dropped below the Add buttons' % TPL)
    # THE BUTTONS STAY. RD-2's Move answers a different question.
    if 'data-move=' not in nt:
        refuse('%s: Move to another day went with the drag handle, and '
               'they are not the same control' % TPL)
    if nt.count('{%') != nt.count('%}'):
        refuse('%s: the tags stopped balancing - %d {%% against %d %%}'
               % (TPL, nt.count('{%'), nt.count('%}')))

    if CHECK:
        print('RO-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        one endpoint, one wrapper, three grips')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RO-1  applied - a day is dragged into order by its grip.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
