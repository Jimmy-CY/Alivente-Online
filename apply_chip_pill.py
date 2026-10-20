# -*- coding: utf-8 -*-
"""apply_chip_pill.py - round CL-1, 20 Oct 2026.

A MEAL IN THE CALENDAR LOOKS LIKE A CHIP AGAIN.

Demetri, testing push 2 on production:

    "The recipes aren't displayed nicely, like they were before. They
     were like pills before."
    "But shouldn't they be like pills?? not just words with a coloured
     background?"

ASKED OF THE BROWSER, which is the only thing that can answer it. Every
rule naming a chip, in cascade order, at 1900px:

    sheet 7  .month-chip            background: var(--alv-accent-soft)
                                    border-left: 2px solid ...
                                    font-size: 11px
    sheet 9  .month-chip, .week-chip  background: transparent
                                      border: 0
                                      font: inherit

SHEET 9 IS RD-2's OWN <style>, and a later stylesheet of equal
specificity wins. So the chip lost its fill, its left bar AND its type
size - `font: inherit` is a shorthand and it resets font-size too. What
is left is 16px plain text, which is exactly what he photographed.

NOTES AND LEFTOVERS SURVIVED, which is the clue that found it:
`.month-chip.is-note` is TWO classes and outranks the reset, so amber
notes and grey leftovers kept their fill while plain recipes went bare.

> RD-2's OWN COMMENT WARNS ABOUT THIS, three properties earlier:
> "A reset that reaches for display is a reset that outranks every
> decision about whether a thing is shown at all."
> It learned that about `display` the same day, took `display` out -
> and left `background`, `border` and `font` doing the identical thing
> to three other decisions.

THE RESET KEEPS ONLY WHAT A BUTTON ACTUALLY NEEDS. A <button> brings a
border, a background, a centred text-align and its own font family.
Of those, the chip rule already owns the background and the type size,
so the reset is cut to the two it does not: the border and the family.
It keeps `cursor` and `text-align`, which nothing else sets.

AND THEY ARE PILLS NOW, which is the half he asked for rather than the
half that was broken. 3px with a 2px left bar is a flat tag; a pill is
round and hugs its word, the way the Side / Frozen / Vegetarian tags on
the Day card already do. The left bar goes with it - a 2px bar on a
999px radius reads as a mistake - and the three colours stay exactly as
they were, because the colour is what says recipe, note or leftover.

Idempotent. Every file backed up to .bak_chippill.
"""
import os
import re
import sys

SUFFIX = '.bak_chippill'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_chip_pill.py'
PATCHER = 'apply_chip_pill.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'CL-1, 20 Oct 2026'
CHECK = False
CREATES = ()

# ---- the pill itself, in the page's own stylesheet
WEEK_WAS = """.week-chip {
    display: block;
    font-size: 11px;
    line-height: 1.35;
    padding: 2px 5px;
    border-radius: 3px;
    border-left: 2px solid var(--alv-accent);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}"""
WEEK_NOW = """.week-chip {
    /* A PILL - CL-1, 20 Oct 2026. Demetri: "shouldn't they be like
       pills?? not just words with a coloured background?" 3px with a
       2px left bar is a flat tag. This is the shape the Side / Frozen
       / Vegetarian tags on the Day card already use, so the calendar
       stops teaching a second vocabulary for the same idea. */
    display: inline-block;
    width: fit-content;
    max-width: 100%;
    /* THE PARENT IS A FLEX COLUMN and its children stretch by
       default, which would make every pill the width of the column
       and undo the hugging. */
    align-self: flex-start;
    font-size: 11px;
    line-height: 1.35;
    padding: 2px 9px;
    border-radius: 999px;
    /* AN EDGE, BECAUSE THE ROW IT SITS ON IS TINTED TOO. accent-soft
       on the highlighted week row is accent-soft on accent-soft, and
       the fill disappeared - the pill read as bare words again, which
       was the complaint. base's own token comment says what this is
       for: "borders on tinted surfaces". */
    border: 1px solid var(--alv-accent-line);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}"""

MONTH_WAS = """.month-chip {
    display: block;
    width: 100%;
    font-size: 11px;
    line-height: 1.35;
    padding: 1px 5px;
    border-radius: 3px;
    border-left: 2px solid var(--alv-accent);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}"""
MONTH_NOW = """.month-chip {
    /* A PILL - CL-1, 20 Oct 2026, the same one the week draws. A meal
       does not change shape when you change zoom level, which is the
       rule .week-chip's own comment states. */
    display: inline-block;
    width: fit-content;
    max-width: 100%;
    align-self: flex-start;
    font-size: 11px;
    line-height: 1.35;
    padding: 1px 9px;
    border-radius: 999px;
    border: 1px solid var(--alv-accent-line);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}"""

# The left bar goes, so the colour that painted it goes with it. The
# BACKGROUND and the INK are untouched - the colour is what says which
# of the three kinds a chip is, and that was never the fault.
WNOTE_WAS = """.week-chip.is-note {
    background: var(--alv-warn-soft);
    color: var(--alv-warn-ink);
    border-left-color: var(--alv-warn);
}"""
WNOTE_NOW = """.week-chip.is-note {
    background: var(--alv-warn-soft);
    border-color: var(--alv-warn-line);
    color: var(--alv-warn-ink);
}"""
WLEFT_WAS = """.week-chip.is-leftover {
    background: var(--alv-surface-deep);
    color: var(--alv-ink-soft);
    border-left-color: var(--alv-neutral);
}"""
WLEFT_NOW = """.week-chip.is-leftover {
    background: var(--alv-surface-deep);
    border-color: var(--alv-line);
    color: var(--alv-ink-soft);
}"""
MNOTE_WAS = """.month-chip.is-note {
    background: var(--alv-warn-soft);
    color: var(--alv-warn-ink);
    border-left-color: var(--alv-warn);
}"""
MNOTE_NOW = """.month-chip.is-note {
    background: var(--alv-warn-soft);
    border-color: var(--alv-warn-line);
    color: var(--alv-warn-ink);
}"""
MLEFT_WAS = """.month-chip.is-leftover {
    background: var(--alv-surface-deep);
    color: var(--alv-ink-soft);
    border-left-color: var(--alv-neutral);
}"""
MLEFT_NOW = """.month-chip.is-leftover {
    background: var(--alv-surface-deep);
    border-color: var(--alv-line);
    color: var(--alv-ink-soft);
}"""

# ---- RD-2's reset, cut to what a button actually needs
RESET_WAS = """.month-chip, .week-chip {
    width: 100%;
    border: 0;
    background: transparent;
    text-align: left;
    font: inherit;
    cursor: pointer;"""
RESET_NOW = """.month-chip, .week-chip {
    /* CUT TO WHAT A BUTTON ACTUALLY NEEDS - CL-1, 20 Oct 2026.
       This <style> is a LATER stylesheet than the one holding the
       chip, so every property named here beats the chip's own at equal
       specificity. It named four the chip owns:
           width: 100%          the pill hugs its word now
           background           the chip's fill, gone at every width
           the font shorthand   it resets font-size too, so 11px
                                chips rendered at 16px
       What is left is the two things a <button> brings that the chip
       does not set for itself, plus the two nothing else sets.
       The note above this rule is right and was written one property
       too early.
       AND NOT border EITHER. The pill carries a 1px edge now, so a
       reset that zeroed the border would delete it from a later
       stylesheet - which is this bug a second time. */
    font-family: inherit;
    text-align: left;
    cursor: pointer;"""


SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'border-radius: 999px'; What = 'CL-1: a meal in the calendar is a pill again - RD-2 made the chips buttons and reset background, border and font in a LATER stylesheet, which beat the chip own rule and left 16px plain text' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'font: inherit'; Absent = $true; Code = $true; What = 'CL-1: and the shorthand that took the type size with it is gone - font-family is what a button needed, not the whole font' },"""

SUITE_WAS = """    'test_date_bar.py'
)"""
SUITE_NOW = """    'test_date_bar.py',
    # CL-1, 20 Oct 2026 - the chip is a pill. Section 2 RENDERS it and
    # reads the COMPUTED fill and type size, because the fault was a
    # rule that was present in the file and beaten in the browser.
    'test_chip_pill.py'
)"""

TREE_WAS = """    # DB-1, 20 Oct 2026 - 88 rules come back out of a media query that
    # was never closed, and a suite starts asking what media a rule is
    # actually in.
    'test_date_bar.py',
]"""
TREE_NOW = """    # DB-1, 20 Oct 2026 - 88 rules come back out of a media query that
    # was never closed, and a suite starts asking what media a rule is
    # actually in.
    'test_date_bar.py',
    # CL-1, 20 Oct 2026 - the chip is a pill, and a later stylesheet
    # stops overruling the rule that draws it.
    'test_chip_pill.py',
]"""

RD_WAS = """    # DB-1, 20 Oct 2026 - the responsive wrapper that never closed.
    '.bak_datebar',
]"""
RD_NOW = """    # DB-1, 20 Oct 2026 - the responsive wrapper that never closed.
    '.bak_datebar',
    # CL-1, 20 Oct 2026 - a meal in the calendar is a pill again.
    '.bak_chippill',
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
    raise SystemExit('CL-1 REFUSED: %s' % msg)


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

    if 'border-radius: 999px' in t and 'font: inherit' not in t:
        print('CL-1  already applied - a meal in the calendar is a pill.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FAULT MUST BE THERE: a later rule that resets what the
    # chip sets. Asked of the code, not of the comment that explains it.
    code = T.code_only(t)
    if 'font: inherit' not in code:
        refuse('%s: the reset does not use the font shorthand, so this '
               'is not the tree this round was written for' % TPL)
    chip_at = code.index('.month-chip {')
    reset_at = code.index('.month-chip, .week-chip {')
    if reset_at < chip_at:
        refuse('%s: the reset already comes BEFORE the chip rule, so it '
               'no longer beats it and this round has nothing to fix'
               % TPL)

    for was, now, what in (
            (WEEK_WAS, WEEK_NOW, 'the week pill'),
            (MONTH_WAS, MONTH_NOW, 'the month pill'),
            (WNOTE_WAS, WNOTE_NOW, 'the week note'),
            (WLEFT_WAS, WLEFT_NOW, 'the week leftover'),
            (MNOTE_WAS, MNOTE_NOW, 'the month note'),
            (MLEFT_WAS, MLEFT_NOW, 'the month leftover'),
            (RESET_WAS, RESET_NOW, 'the reset')):
        t = swap(t, was, now, '%s (%s)' % (TPL, what))
    out[pt] = t

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s
    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)
    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # CL-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nc = T.code_only(out[pt])

    # THE RESET NO LONGER NAMES WHAT THE CHIP OWNS. Asked property by
    # property of the reset's own body, not of the whole file - the
    # words appear all over this stylesheet.
    body = nc[nc.index('.month-chip, .week-chip {'):]
    body = body[:body.index('}')]
    for prop in ('background', 'font:', 'width:', 'border'):
        if prop in body:
            refuse('%s: the reset still sets %s, which the chip owns '
                   'and which a later stylesheet would win' % (TPL, prop))
    for prop in ('cursor: pointer', 'text-align'):
        if prop not in body:
            refuse('%s: the reset dropped %s, which a <button> really '
                   'does need' % (TPL, prop))
    # AND EVERY PILL HAS AN EDGE, which is what makes it read on the
    # tinted week row rather than only on white.
    if nc.count('border: 1px solid var(--alv-accent-line)') != 2:
        refuse('%s: %d pill edge(s), expected 2'
               % (TPL, nc.count('border: 1px solid var(--alv-accent-line)')))

    # BOTH CHIPS ARE PILLS, and both say so the same way.
    if nc.count('border-radius: 999px') != 2:
        refuse('%s: %d pill radius(es), expected 2 - the month and the '
               'week draw the same chip'
               % (TPL, nc.count('border-radius: 999px')))
    # AND NO LEFT BAR SURVIVES ON ONE OF THEM, which would be the two
    # views disagreeing about what a meal looks like.
    if 'border-left-color: var(--alv-warn)' in nc or \
            'border-left: 2px solid var(--alv-accent)' in nc:
        refuse('%s: a chip still carries the left bar' % TPL)

    # THE THREE COLOURS ARE UNTOUCHED. The fill is what says which kind
    # of thing a chip is and this round changes only the shape.
    for tok in ('var(--alv-accent-soft)', 'var(--alv-warn-soft)',
                'var(--alv-surface-deep)'):
        if nc.count(tok) < 2:
            refuse('%s: %s is no longer on both chips' % (TPL, tok))

    if CHECK:
        print('CL-1  --check: %d file(s) would change, none written.'
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
    print('CL-1  applied - a meal in the calendar is a pill again.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
