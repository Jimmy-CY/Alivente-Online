# -*- coding: utf-8 -*-
"""apply_week_drag.py - round WD-1, 22 Oct 2026.

THE WEEK'S SEVEN COLUMNS DRAG INTO ORDER TOO.

RO-1 shipped drag-to-reorder on the Day card on 21 October and left
the Week view alone, deliberately, with the question put to Demetri.
He answered on 22 October: yes, add it.

NO NEW MACHINERY. reorder_meal_day already takes a date and an order
and already refuses an order that is not exactly the rows on that
date. A week column IS a date. This round is markup, a stylesheet rule
and a binding - the endpoint, its gates and its suite are RO-1's and
untouched.

THE CHIP IS THE HANDLE, AND THAT IS A DIFFERENT IDIOM FROM THE DAY
CARD, ON PURPOSE. A day row carries a thumbnail, a stepper and four
icon buttons, so a drag needs its own grip or it competes with all of
them. A week column is 152px wide at 1200px - MV-3 measured it and
refused to put a stepper or row actions there for exactly that reason
- and a chip in it has one interaction, its menu. There is no room for
a grip and nothing for it to disambiguate. So the chip drags itself.

WITHIN A COLUMN ONLY. Each column is its own Sortable with no shared
group, so nothing crosses from Tuesday to Wednesday. That is not a
limitation this round ran out of time for: dragging between columns
writes a DIFFERENT thing - a date, not an order - and that is what
Move on the chip menu already does, with leftovers travelling with
their meal. One gesture that silently does either depending on where
the pointer lands is how a plan gets quietly rearranged. It is the
next round if he wants it, and the guide now names it as what is
coming.

THE CLICK AFTER A DRAG IS SWALLOWED. RD-2's chip menu opens from a
capturing listener on the document, which is the only place one
delegated handler can get in front of an inline onclick further down
the tree. Without a guard, every drop would open the menu of whatever
was dropped - so the listener now returns early if a drag ended within
the last 300ms. The flag is cleared by time rather than by the next
click, because a drop that lands outside any chip produces no click at
all and a flag cleared by a click that never comes stays set for ever.

AND THE PICKER IS SAFE FOR THE SAME REASON. .week-col-body carries an
inline onclick that opens the picker on the day; the same early return
covers it, because the capturing listener runs first.

A PHONE HAS NO WEEK GRID TO DRAG, AND THAT IS MV-3's DESIGN, NOT THIS
ROUND RUNNING OUT OF ROOM. Below 768px .week-grid is display:none and
.day-strip takes over - seven buttons and the Day card beneath them -
so the reorder gesture on a phone is RO-1's grip on that card, which
test_day_order already measures at 390px. The suite asks a 390px
Chromium for the grid's computed display, so that stays a decision
somebody made rather than something nobody looked at.

AND IT ADDS NO PERMISSION LOCK, HAVING MEASURED FOR ONE. See the note
above the gates: reorder_meal_day is edit-tier, so the first draft put
a flag on both bindings - and then the template said both bindings were
already inside {% if perms.auth.can_edit_recipes %}. What shipped is a
gate asking whether that block really encloses the new binding, which
nothing pinned before.

Idempotent. Every file backed up to .bak_weekdrag.
"""
import os
import re
import sys

SUFFIX = '.bak_weekdrag'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
GUIDE = os.path.join('pages', 'help_content', 'administration.html')
G3 = 'test_meal_guide3.py'
G5 = 'test_meal_guide5.py'
MH = 'test_meal_help.py'
RO = 'test_day_order.py'
ME = 'test_week_drag.py'
PATCHER = 'apply_week_drag.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'WD-1, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE MARKUP - the column body carries its own date
# ==========================================================================
BODY_WAS = """                        <div class="week-col-body"
                             {% if perms.auth.can_edit_recipes %}role="button" tabindex="0"""

BODY_NOW = """                        {# data-day - WD-1, 22 Oct 2026. The column IS a   #}
                        {# date, and reorder_meal_day asks for one: an     #}
                        {# order only means anything about a day.          #}
                        <div class="week-col-body"
                             data-day="{{ day.date|date:'Y-m-d' }}"
                             {% if perms.auth.can_edit_recipes %}role="button" tabindex="0"""

# ==========================================================================
# THE RULES
# ==========================================================================
CSS_WAS = """/* DRAGGING A DAY INTO ORDER - RO-1, 21 Oct 2026."""

CSS_NOW = """/* AND THE WEEK'S COLUMNS - WD-1, 22 Oct 2026.

   NO GRIP HERE. A column is 152px at 1200px, which is why MV-3 put
   neither a stepper nor row actions in one, and a chip in it has a
   single interaction. The chip drags itself; there is no room for a
   handle and nothing for one to disambiguate.

   HIDDEN BEHIND THE SAME CLASS AS THE DAY CARD. .is-draggable is only
   added once Sortable has really answered, so a failed CDN leaves the
   week exactly as it was - chips that open their menu and nothing
   that looks draggable and is not.

   THE CHOSEN CHIP GETS A RING AND NOT A FILL, which is where this
   round differs from the day card on purpose. RO-1 marks a chosen ROW
   with --alv-surface, and that works because a row has no fill of its
   own. A week chip does: accent-soft normally, warn-soft for a note,
   surface-deep for a leftover. The first draft of this rule copied
   RO-1 and set the chosen background to accent-soft - which is what a
   normal chip ALREADY IS. Measured in CIE Lab it came out at dE 0.0,
   an invisible state, and the renders are what caught it.

   A FILL CANNOT WIN HERE. accent-line reads at dE 15.9 / 27.4 / 18.0
   against the three chip fills, so it is detectable - but ink-soft on
   it measures 3.57:1, and the leftover chip's own text would go under
   the floor at 11px. The fill carries MEANING on this chip; the ring
   does not have to. accent-ink is dE 60+ from all three fills, leaves
   every chip's own colours alone, and says the same thing. */
.week-col-body.is-draggable .week-chip { cursor: grab; touch-action: none; }
.week-col-body.is-draggable .week-chip:active { cursor: grabbing; }
.week-col-body .sortable-ghost { opacity: 0.4; }
.week-col-body .sortable-drag { opacity: 0.9; }
.week-col-body .sortable-chosen {
    box-shadow: 0 0 0 2px var(--alv-accent-ink);
}

/* DRAGGING A DAY INTO ORDER - RO-1, 21 Oct 2026."""

# ==========================================================================
# THE CLICK AFTER A DROP
# ==========================================================================
GUARD_WAS = """    document.addEventListener('click', function (e) {
        var chip = e.target.closest('[data-chip]');
        if (chip) {"""

GUARD_NOW = """    document.addEventListener('click', function (e) {
        // A DROP IS NOT A CLICK - WD-1, 22 Oct 2026.
        //
        // Sortable fires a click on the element that was dragged, and
        // this listener captures, so without the guard every drop in
        // the week view opened the menu of whatever was dropped. The
        // same return covers .week-col-body's inline onclick, which
        // would otherwise open the picker.
        //
        // CLEARED BY TIME, NOT BY THE NEXT CLICK. A drop that lands
        // outside any chip produces no click at all, and a flag
        // cleared by a click that never comes stays set for ever.
        if (window.__alvDragEnded
                && Date.now() - window.__alvDragEnded < 300) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        var chip = e.target.closest('[data-chip]');
        if (chip) {"""

# ==========================================================================
# WHO MAY DRAG, AND WHY THIS ROUND ADDS NOTHING FOR IT.
#
# The first draft of this round added a permission flag to both
# bindings, on the reasoning that reorder_meal_day is edit-tier and
# RO-1 bound the day card for everybody who could SEE the planner - so
# a view-only member could grip a meal, drag the day into a new order,
# and watch the page reload it back.
#
# THEN IT WAS MEASURED, AND IT WAS ALREADY TRUE. Both bindings sit
# inside the {% if perms.auth.can_edit_recipes %} block that opens
# above openPicker and closes 800 lines later. A reader is served a
# page with the chips on it and no binding at all; ALV_MAY_ORDER would
# have been a second lock on a door that was already locked, and a
# suite claiming it fixed something would have been claiming a bug
# that did not exist. Removed, and the gate below asks the template
# whether the block really does enclose the new binding - because
# NOTHING pinned that until now, and a later round that moves the
# script out of the block would take the lock with it.
# ==========================================================================
# ==========================================================================
# THE BINDING
# ==========================================================================
JS_WAS = """// WHAT THE DROP SENDS. The ids in the order they now sit in, and the
// day they sit on - the endpoint will not take one without the other."""

JS_NOW = """// ------------------------------------------- dragging a week column
// WD-1, 22 Oct 2026. Demetri, asked on 21 October and answered on 22:
// yes, the week too.
//
// ONE SORTABLE PER COLUMN, WITH NO SHARED GROUP, so nothing crosses
// from Tuesday to Wednesday. Dragging between columns writes a DATE
// and not an order, which is what Move on the chip menu already does.
//
// THE SAME ENDPOINT AS THE DAY CARD. A column is a date, and
// reorder_meal_day has taken a date and an order since RO-1 - it
// refuses an order that is not exactly the rows on that date, which
// is as true of a column as of a card.
(function () {
    if (typeof Sortable === 'undefined') { return; }
    var cols = document.querySelectorAll('.week-col-body[data-day]');
    if (!cols.length) { return; }
    [].forEach.call(cols, function (col) {
        if (!col.querySelector('.week-chip')) { return; }
        col.classList.add('is-draggable');
        new Sortable(col, {
            draggable: '.week-chip',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            chosenClass: 'sortable-chosen',
            animation: 150,
            onStart: function () { window.__alvDragEnded = 0; },
            onEnd: function () {
                window.__alvDragEnded = Date.now();
                saveColumnOrder(col);
            }
        });
    });
}());

function saveColumnOrder(col) {
    var ids = [].map.call(col.querySelectorAll('[data-chip]'),
        function (c) { return c.getAttribute('data-chip'); });
    if (!ids.length) { return; }
    var body = new FormData();
    body.append('date', col.getAttribute('data-day'));
    body.append('order', ids.join(','));
    body.append('csrfmiddlewaretoken', '{{ csrf_token }}');
    fetch('{% url "reorder_meal_day" %}', {
        method: 'POST', credentials: 'same-origin', body: body
    })
        .then(function (r) {
            // 409 MEANS THE DAY CHANGED UNDER US - RO-1's answer, and
            // the same one applies here: this column is looking at
            // something that is no longer true.
            if (r.status === 409) { window.location.reload(); return null; }
            if (!r.ok) { throw new Error(r.status); }
            return r.json();
        })
        .catch(function () { window.location.reload(); });
}

// WHAT THE DROP SENDS. The ids in the order they now sit in, and the
// day they sit on - the endpoint will not take one without the other."""

# ==========================================================================
# THE GUIDE - the promise RO-1 made, kept
# ==========================================================================
GUIDE_WAS = """      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use. <strong>Not yet, and coming:</strong> reordering the week view. Moving a meal from day to day, which stood here beside it, is <strong>Move</strong> on the chip menu now."""

GUIDE_NOW = """      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use - and in the week view the meals themselves drag up and down their own column. <strong>Not yet, and coming:</strong> dragging a meal from one day to another. That writes a date rather than an order, so for now it is <strong>Move</strong> on the chip menu."""

# The bare line is NOT a unique anchor: this suite quotes test_meal_guide3's
# copy of it in section 4, so the file holds the words twice. The anchor
# carries the comment line above it, which only the declaration has.
G5_OUT_WAS = """# with Demetri and unanswered, and RO-1 explicitly does not do it.
OUTSTANDING = 'reordering the week view'"""

G5_OUT_NOW = """# with Demetri and unanswered, and RO-1 explicitly does not do it.
# WD-1, 22 Oct 2026 - THE WEEK REORDERS NOW, so the promise moves on
# again. What is genuinely not built is dragging a meal ACROSS days:
# that writes a date and not an order, which is Move's job, and one
# gesture doing either depending on where the pointer lands is how a
# plan gets quietly rearranged.
OUTSTANDING = 'dragging a meal from one day to another'"""

G3_SAY_WAS = """    c['  reordering a day too'] = (
        any('reordering' in s.lower() for s in coming))"""

# RO-1 asked whether the coming sentence was about REORDERING, because
# what was outstanding then was a reorder - the week's columns. What is
# outstanding now is a MOVE, so the word reordering has no business in
# the promise box any more, and a claim that still demanded it would be
# demanding the guide promise something that is already built.
G3_SAY_NOW = """    # WD-1, 22 Oct 2026 - the coming sentence is no longer about
    # reordering anything: the week reorders. It is about crossing days,
    # which writes a date. Asking for the word 'reordering' here would
    # ask the guide to keep promising a thing that now ships.
    c['  and it is about crossing days, not ordering them'] = (
        any('from one day to another' in s.lower() for s in coming)
        and not any('reordering' in s.lower() for s in coming))"""

G3_OUT_WAS = """# RO-1, 21 Oct 2026 - the day can be dragged now; the week cannot.
OUTSTANDING = 'reordering the week view'"""

G3_OUT_NOW = """# RO-1, 21 Oct 2026 - the day can be dragged now; the week cannot.
# WD-1, 22 Oct 2026 - and now it can. Across days is what is left.
OUTSTANDING = 'dragging a meal from one day to another'"""

G5_PIN_WAS = """    c['  and its outstanding pin moved to reordering'] = (
        "OUTSTANDING = 'reordering the week view'" in g3)"""

G5_PIN_NOW = """    c['  and its outstanding pin moved to reordering'] = (
        "OUTSTANDING = 'dragging a meal from one day to another'" in g3)"""

# RO-1's OWN SUITE CLOSES BY SAYING THE WEEK CANNOT BE DRAGGED. It is
# printed prose and no claim reads it, so nothing would have failed -
# which is exactly why it is worth moving. A suite that prints something
# untrue about the tree it is run against is a suite nobody believes the
# rest of.
RO_SAY_WAS = """print('  Not that the WEEK view can be dragged. It cannot. The Day')
print('  card is what Demetri asked about and what was agreed; the')
print('  seven columns are a separate question, asked and not yet')
print('  answered.')"""

RO_SAY_NOW = """print('  Not that the WEEK view can be dragged - WD-1 does that, on')
print('  22 October, through this round endpoint, and test_week_drag')
print('  is where it is proved. What this round proves is the Day')
print('  card, which is what Demetri asked about first.')"""

MH_WAS = """    ok(any('reordering the week view' in s.lower()"""

MH_NOW = """    ok(any('dragging a meal from one day to another' in s.lower()"""

G5_CTL_WAS = """ok('def reorder_meal_day' in view and 'def reorder_week' not in view,
   'CONTROL: a DAY can be reordered now and a WEEK cannot, so the one '"""

G5_CTL_NOW = """ok('def reorder_meal_day' in view and 'def move_meal_entry' in view,
   'CONTROL: ordering and MOVING are two endpoints, which is why one '"""

MH_CTL_WAS = """    ok('def reorder_meal_day' in view_py
       and 'def reorder_week' not in view_py,
       '  CONTROL: a day reorders and a week does not, which is what '
       'the guide says')"""

MH_CTL_NOW = """    # WD-1, 22 Oct 2026 - the week reorders too, through the SAME
    # endpoint, because a column is a date. What is still not built is
    # dragging ACROSS days, and the thing that would do it is a date
    # write - move_meal_entry - not an order write.
    ok('def reorder_meal_day' in view_py
       and 'def reorder_week' not in view_py,
       '  CONTROL: one endpoint orders a date, whichever view you are '
       'looking at it in')"""


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
    raise SystemExit('WD-1 REFUSED: %s' % msg)


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

    pt = os.path.join(root, TPL)
    t = read(pt)

    if MARK in t:
        print('WD-1  already applied - the week columns drag.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE ENDPOINT IS RO-1's AND THIS ROUND ADDS NONE.
    pv = os.path.join(root, 'pages', 'views', 'recipes', 'meal_planning.py')
    v = T.python_code_only(read(pv), payloads=True)
    if 'def reorder_meal_day' not in v:
        refuse('reorder_meal_day is gone - this round reuses RO-1 '
               'endpoint and cannot reuse what is not there')
    if 'def move_meal_entry' not in v:
        refuse('move_meal_entry is gone, and it is what this round '
               'deliberately does NOT duplicate')

    t = swap(t, BODY_WAS, BODY_NOW, '%s (the date)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the rules)' % TPL)
    t = swap(t, GUARD_WAS, GUARD_NOW, '%s (the guard)' % TPL)
    t = swap(t, JS_WAS, JS_NOW, '%s (the binding)' % TPL)
    out[pt] = t

    pg = os.path.join(root, GUIDE)
    out[pg] = swap(read(pg), GUIDE_WAS, GUIDE_NOW, '%s (the promise)' % GUIDE)

    p5 = os.path.join(root, G5)
    g5 = read(p5)
    g5 = swap(g5, G5_OUT_WAS, G5_OUT_NOW, '%s (outstanding)' % G5)
    g5 = swap(g5, G5_PIN_WAS, G5_PIN_NOW, '%s (the pin)' % G5)
    g5 = swap(g5, G5_CTL_WAS, G5_CTL_NOW, '%s (the control)' % G5)
    out[p5] = g5

    p3 = os.path.join(root, G3)
    g3 = read(p3)
    g3 = swap(g3, G3_OUT_WAS, G3_OUT_NOW, '%s (outstanding)' % G3)
    g3 = swap(g3, G3_SAY_WAS, G3_SAY_NOW, '%s (the promise claim)' % G3)
    out[p3] = g3

    pr = os.path.join(root, RO)
    out[pr] = swap(read(pr), RO_SAY_WAS, RO_SAY_NOW,
                   '%s (what it does not prove)' % RO)

    pm = os.path.join(root, MH)
    mh = read(pm)
    mh = swap(mh, MH_WAS, MH_NOW, '%s (the promise)' % MH)
    mh = swap(mh, MH_CTL_WAS, MH_CTL_NOW, '%s (the control)' % MH)
    out[pm] = mh

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_help_agrees.py'
)""", """    'test_help_agrees.py',
    # WD-1, 22 Oct 2026 - the week columns drag, through RO-1 endpoint.
    'test_week_drag.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/help_content/administration.html'; Text = 'how far into the menu';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'saveColumnOrder'; What = 'WD-1: the week view seven columns drag into order through reorder_meal_day, the endpoint RO-1 built - a column is a date. Within a column only: across days writes a date and that is Move' },
    @{ File = 'pages/help_content/administration.html'; Text = 'how far into the menu';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # HG-1, 22 Oct 2026 - the guide and the page agree, both ways.
    'test_help_agrees.py',
]""", """    # HG-1, 22 Oct 2026 - the guide and the page agree, both ways.
    'test_help_agrees.py',
    # WD-1, 22 Oct 2026 - the week drags too.
    'test_week_drag.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # HG-1, 22 Oct 2026 - the guide describes what shipped.
    '.bak_helpagrees',
]""", """    # HG-1, 22 Oct 2026 - the guide describes what shipped.
    '.bak_helpagrees',
    # WD-1, 22 Oct 2026 - the week columns drag.
    '.bak_weekdrag',
]""", '%s (ROUNDS)' % ROUNDS)

    pwd = os.path.join(root, WD)
    wd = read(pwd)
    n = re.search(r'CONVERTED_N = (\d+)', wd)
    out[pwd] = swap(wd, 'CONVERTED_N = %s' % n.group(1),
                    'CONVERTED_N = %d   # WD-1, 22 Oct 2026 - this round '
                    'own suite   # (was %s)'
                    % (int(n.group(1)) + 1, n.group(1)),
                    '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nt = out[pt]
    js = T.code_only_js(nt)
    if "typeof Sortable === 'undefined'" not in js:
        refuse('%s: the week binding does not guard on the library' % TPL)
    if "draggable: '.week-chip'" not in js:
        refuse('%s: the column sortable does not restrict to chips' % TPL)
    # THE BINDING IS INSIDE THE EDIT-TIER BLOCK, measured rather than
    # assumed - see the note above WHO MAY DRAG. A reader is served the
    # chips and no binding, and that is where the lock is.
    at = nt.index("document.querySelectorAll('.week-col-body[data-day]')")
    depth, enclosing = 0, []
    for m in re.finditer(r'\{%\s*(if|endif)\b([^%]*)%\}', nt[:at]):
        if m.group(1) == 'if':
            depth += 1
            enclosing.append(m.group(2).strip())
        else:
            depth -= 1
            if enclosing:
                enclosing.pop()
    if 'perms.auth.can_edit_recipes' not in enclosing:
        refuse('%s: the week binding is NOT inside the edit-tier block - '
               'a reader would be served a drag that cannot write. '
               'enclosing: %r' % (TPL, enclosing))
    # NO SHARED GROUP. One word would let a meal cross to another day
    # and write nothing about it.
    cols = js[js.index('var cols = document.querySelectorAll'):]
    cols = cols[:cols.index('function saveColumnOrder')]
    if 'group' in cols:
        refuse('%s: the column sortable names a GROUP, which would let '
               'a meal cross days and write an order instead of a date'
               % TPL)
    # THE DROP IS NOT A CLICK.
    # check_gates flags this one: the four mentions it counts are the four
    # this round writes - two in GUARD_NOW (the read) and two in JS_NOW
    # (the clear and the set). That is the point. The gate is not asking
    # whether the tree already had a flag; it is asking whether BOTH halves
    # of mine landed, because a set with no read swallows nothing and a read
    # with no set swallows every click. Three is the floor, not the count,
    # so a later round may add a fifth mention without tripping it.
    if '__alvDragEnded' not in js:
        refuse('%s: nothing stops the drop opening a menu' % TPL)
    if js.count('__alvDragEnded') < 3:
        refuse('%s: the flag is set or read but not both' % TPL)
    # AND MOVE IS STILL THERE.
    if 'askMove(' not in js:
        refuse('%s: Move went with the drag, and they are not the same '
               'control' % TPL)
    if nt.count('{%') != nt.count('%}'):
        refuse('%s: the tags stopped balancing - %d {%% against %d %%}'
               % (TPL, nt.count('{%'), nt.count('%}')))
    # THE GUIDE PROMISES SOMETHING THAT IS REALLY NOT BUILT.
    ng = out[pg]
    if 'reordering the week view' in ng:
        refuse('%s: the guide still names the week as coming' % GUIDE)
    if 'dragging a meal from one day to another' not in ng:
        refuse('%s: the guide promises nothing, and one thing really is '
               'not built' % GUIDE)

    if CHECK:
        print('WD-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        one sortable per column, no group, no new endpoint')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('WD-1  applied - the week columns drag into order.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
