# -*- coding: utf-8 -*-
"""apply_pick_note.py - round NT-1, 20 Oct 2026.

A NOTE, FROM MONTH AND WEEK.

Demetri: "How can I add a Note or Leftovers from the month view or the
week view??"

LO-1 answered the leftovers half by putting them on the chip menu,
which is where a verb that acts on a MEAL belongs. A note does not act
on a meal - it belongs to a DAY - so it goes where days are added to:
the picker.

HIS ANSWER WAS "each to the control that already fits", and the
picker fits. It is already the add-something-to-this-day dialog, it
already knows which day it is on, and since PS-1 it already stays open
with that day's rows listed underneath. A note joins that strip like
anything else.

NOTHING NEW IS BUILT. openNote(dateStr, dayName) has existed since
MO-1 and takes exactly the two things the picker is holding:

    #pickerDate      the day
    #pickerDayName   what to call it

THE ONE HARD PART IS THE HAND-OFF, and it is PS-1's doing. The picker
reloads the page when it closes if anything was added - that is RL-1's
repaired handler - and a reload in the middle of opening the note
dialog would take the note dialog with it. So the flag is CARRIED:
cleared before the picker hides, and spent when the note dialog is
dismissed. If the note is submitted instead, the form posts and the
page reloads anyway, with both the meals and the note on it.

TWO MODALS ARE NOT STACKED. Bootstrap 4 does not handle that without
help, and a dialog over a dialog is a worse answer than a hand-off.
The second opens only once the first has finished closing, which is
what `one('hidden.bs.modal')` is for.

Idempotent. Every file backed up to .bak_picknote.
"""
import os
import re
import sys

SUFFIX = '.bak_picknote'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_pick_note.py'
PATCHER = 'apply_pick_note.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'NT-1, 20 Oct 2026'
CHECK = False
CREATES = ()

BTN_WAS = """                    <span class="picker-hint" id="pickerHint">Click a recipe to add it.</span>
                    <button type="button" class="btn action-primary" id="pickerDone"
                            onclick="closePicker()">Done</button>"""
BTN_NOW = """                    <span class="picker-hint" id="pickerHint">Click a recipe to add it.</span>
                    {# A NIGHT YOU ARE NOT COOKING - NT-1, 20 Oct 2026. #}
                    {# Demetri asked how to add a note from Month or    #}
                    {# Week; openNote was reachable only from the Day    #}
                    {# card. A note belongs to a DAY, and this dialog is #}
                    {# the one that adds things to a day.                #}
                    <button type="button" class="btn action-secondary" id="pickerNote">
                        <i class="fas fa-store"></i> Add a note instead
                    </button>
                    <button type="button" class="btn action-primary" id="pickerDone"
                            onclick="closePicker()">Done</button>"""

JS_WAS = """function openNote(dateStr, dayName) {"""
JS_NOW = """// THE HAND-OFF FROM THE PICKER - NT-1, 20 Oct 2026.
//
// DELEGATED, so it does not care when the footer was drawn, and in a
// block that cannot be taken down by somebody else's line.
//
// THE DIRTY FLAG IS CARRIED, NOT IGNORED. PS-1 reloads the page when
// the picker closes having added something, and that reload would
// arrive in the middle of opening this dialog and take it with it.
// So it is cleared before the picker hides and spent when the note
// dialog is DISMISSED. If the note is submitted instead, the form
// posts and the page reloads anyway - with the meals and the note on
// it.
//
// jQuery IS ASKED FOR AT CLICK TIME, not at parse time. RL-1 spent a
// day on the difference: base loads it near the end of the document,
// so a guard that runs while the page is parsing finds nothing and
// binds nothing for ever. By the time somebody presses a button it is
// certainly there - and it is still guarded, because a page without
// it should not throw.
document.addEventListener('click', function (e) {
    if (!e.target.closest('#pickerNote')) { return; }
    var when = document.getElementById('pickerDate');
    var name = document.getElementById('pickerDayName');
    if (!when || !name || !window.jQuery) { return; }
    var dateStr = when.value;
    var dayName = name.textContent;
    var carried = (typeof pickerDirty !== 'undefined') && pickerDirty;
    pickerDirty = false;
    var $picker = window.jQuery('#pickerModal');
    $picker.one('hidden.bs.modal', function () {
        openNote(dateStr, dayName);
        if (carried) {
            // ONE SHOT. If they dismiss the note the calendar behind
            // is stale by however many meals they just added, so the
            // reload PS-1 would have done happens here instead.
            window.jQuery('#noteModal').one('hidden.bs.modal',
                function () { window.location.reload(); });
        }
    });
    $picker.modal('hide');
});

function openNote(dateStr, dayName) {"""


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
    raise SystemExit('NT-1 REFUSED: %s' % msg)


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

    if 'id="pickerNote"' in t:
        print('NT-1  already applied - a note can be added from the picker.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)
    js = T.code_only_js(t)

    # ---- THE GROUND: the picker, the dialog, and the two fields the
    # hand-off reads. Each asked for by name, because a hand-off that
    # reads an element which is not there fails silently.
    for probe, why in (
            ('id="pickerModal"', 'the picker'),
            ('id="noteModal"', 'the note dialog MO-1 built'),
            ('id="pickerDate"', 'the field holding the day'),
            ('id="pickerDayName"', 'the field holding its name')):
        if probe not in code:
            refuse('%s: %s is missing (%s)' % (TPL, probe, why))
    if not re.search(r'function openNote\(', js):
        refuse('%s: openNote is not defined, so the button would call '
               'nothing' % TPL)
    if 'pickerDirty' not in js:
        refuse('%s: PS-1 has not run, so there is no dirty flag to '
               'carry across the hand-off' % TPL)

    t = swap(t, BTN_WAS, BTN_NOW, '%s (the button)' % TPL)
    t = swap(t, JS_WAS, JS_NOW, '%s (the hand-off)' % TPL)
    out[pt] = t

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_chip_left.py'
)""", """    'test_chip_left.py',
    # NT-1, 20 Oct 2026 - a note from Month and Week. Section 3
    # drives the hand-off, because two dialogs and a reload is
    # exactly where this goes wrong.
    'test_pick_note.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-act="leftovers"';""",
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerNote"'; What = 'NT-1: a note can be added from Month and Week - openNote was reachable only from the Day card, and a note belongs to a DAY so it joins the dialog that adds things to one' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'data-act="leftovers"';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # LO-1, 20 Oct 2026 - leftovers join the chip menu, so the verb
    # is reachable from every view rather than one.
    'test_chip_left.py',
]""", """    # LO-1, 20 Oct 2026 - leftovers join the chip menu, so the verb
    # is reachable from every view rather than one.
    'test_chip_left.py',
    # NT-1, 20 Oct 2026 - and a note joins the picker, which is the
    # dialog that adds things to a day.
    'test_pick_note.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # LO-1, 20 Oct 2026 - leftovers from Month and Week.
    '.bak_chipleft',
]""", """    # LO-1, 20 Oct 2026 - leftovers from Month and Week.
    '.bak_chipleft',
    # NT-1, 20 Oct 2026 - a note from Month and Week.
    '.bak_picknote',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # NT-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nc = T.code_only(out[pt])
    njs = T.code_only_js(out[pt])

    # COUNTED AS AN ELEMENT, not as a string - LO-1 paid this an hour
    # ago, when a JavaScript selector counted as a second button.
    if len(re.findall(r'<button[^>]*id="pickerNote"', nc)) != 1:
        refuse('%s: expected exactly one note button in the picker'
               % TPL)

    # THE HAND-OFF WAITS. Opening the second dialog before the first
    # has finished closing is two modals, which Bootstrap 4 does not
    # do without help.
    if "one('hidden.bs.modal'" not in njs:
        refuse('%s: the note dialog is opened without waiting for the '
               'picker to close' % TPL)

    # AND THE DIRTY FLAG IS CARRIED RATHER THAN DROPPED. Clearing it
    # without spending it would lose the reload PS-1 owes, and the
    # calendar would sit stale behind the note dialog.
    hand = njs[njs.index("closest('#pickerNote')"):][:1800]
    if 'pickerDirty = false' not in hand:
        refuse('%s: the hand-off does not stop PS-1 reloading mid-way'
               % TPL)
    if 'location.reload' not in hand:
        refuse('%s: the hand-off clears the dirty flag and never '
               'spends it, so an add made just before the note would '
               'leave the calendar stale' % TPL)

    if CHECK:
        print('NT-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('NT-1  applied - a note from Month and Week.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
