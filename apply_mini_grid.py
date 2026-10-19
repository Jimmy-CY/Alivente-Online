# -*- coding: utf-8 -*-
"""apply_mini_grid.py - round MC-4, 19 Oct 2026.

RELEASE 3, PUSH 2. THE MINI CALENDAR IS A CALENDAR.

Demetri, 19 Oct, testing the live planner: "There is something wrong
here ...." - with a screenshot of October 2026 drawn as a single
vertical column of thirty-one numbers under seven weekday headers.

THE FAULT, IN ONE SENTENCE. `.mini-calendar-grid` is a seven-column
grid that CLOSES after the seven weekday headers, so every week row is
a SIBLING of the grid rather than a child of it - and each row carries
`display: contents`, which dissolves the row and hands its seven day
cells to the row's PARENT. The parent is `.mini-calendar`, which is not
a grid. So thirty-five block-level day cells stack in one column.

    <div class="mini-calendar-grid">
        ...seven headers...
    </div>              <-- the grid ends here

    {% for week in calendar_weeks %}
    <div class="mini-calendar-week">   <-- display: contents
        ...seven days...
    </div>
    {% endfor %}

display: contents is right and the rows should keep it: it is what lets
`.mini-calendar-week.selected .mini-calendar-day` paint a whole week
while the cells still belong to one seven-column grid. The row just has
to be INSIDE the grid for that to mean anything. One `</div>` moves.

WHY NOBODY CAUGHT IT, which is the part worth keeping. NO SUITE HAS
EVER RENDERED THIS CALENDAR. test_planner asserts the string
'mini-calendar-week selected' is in the page; MD-1's D26 asserts the
view normalises a week to a Monday so the row can match. Both are true
and both passed on every push. Neither of them looks at the picture,
and a layout fault is only visible in the picture.

AND IT WAS RENDERED, BY ME, AN HOUR BEFORE HE REPORTED IT. MW-1's
before-and-after render drew this column in both halves, and I read
"the same in the before and the after" as "the test harness" rather
than "not THIS push". Those are different sentences. A thing that is
broken in the before and the after is not a thing this round broke; it
is still a thing that is broken.

So this round ships a suite that RENDERS the calendar and counts what
is in each column, and the suite is what makes the fix a fact rather
than a hope.

Idempotent. Every file backed up to .bak_minigrid.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_minigrid'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_mini_grid.py'
PATCHER = 'apply_mini_grid.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MC-4, 19 Oct 2026'
CHECK = False


# ============================================================ THE MARKUP
# THE GRID CLOSES AFTER THE LOOP, NOT BEFORE IT. The whole fix.
GRID_WAS = """                    <div class="mini-calendar-day-header">Su</div>
                </div>

                {% for week in calendar_weeks %}"""
GRID_NOW = """                    <div class="mini-calendar-day-header">Su</div>

                {# THE WEEKS GO INSIDE THE GRID - MC-4, 19 Oct 2026, and  #}
                {# the grid used to close on the line above this one.     #}
                {# Each row wears display: contents so that a whole week  #}
                {# can be painted by one rule while its seven cells still #}
                {# sit in one seven-column grid - and display: contents   #}
                {# hands the cells to the row's PARENT. With the grid     #}
                {# closed above, that parent was .mini-calendar, which is #}
                {# not a grid, so thirty-five day cells stacked in one    #}
                {# column. Demetri found it on the live site.             #}
                {% for week in calendar_weeks %}"""

GRID_END_WAS = """                </div>
                {% endfor %}

                <div class="calendar-legend">"""
GRID_END_NOW = """                </div>
                {% endfor %}
                </div>{# .mini-calendar-grid - MC-4, 19 Oct 2026 #}

                <div class="calendar-legend">"""


# =============================================================== THE CSS
# A NOTE WHERE THE RULE IS, because the next person to touch this
# markup is the one who needs it.
CSS_WAS = """.mini-calendar-week {
    display: contents;
    cursor: pointer;
}"""
CSS_NOW = """/* display: contents, AND THE ROW MUST BE INSIDE THE GRID - MC-4,
   19 Oct 2026. This rule dissolves the row so its seven day cells
   become children of the row's PARENT, which is what lets one grid
   lay out every week while .mini-calendar-week.selected still paints
   a whole row. It is also why the row is not optional furniture: move
   it out of .mini-calendar-grid and the cells are handed to whatever
   is outside, which for four weeks on the live site was a plain div -
   thirty-five cells in one column.

   cursor: pointer belongs to the ROW even though the row draws
   nothing, because the row is what carries the onclick. */
.mini-calendar-week {
    display: contents;
    cursor: pointer;
}"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/help_content/administration.html'; Text = 'Leftovers, and they are free'; What = 'MH-3: and tells the reader the second night costs nothing' },"""
SENT_NOW = """    @{ File = 'pages/help_content/administration.html'; Text = 'Leftovers, and they are free'; What = 'MH-3: and tells the reader the second night costs nothing' },
    # ------------------------------------------------- MC-4, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEKS GO INSIDE THE GRID'; What = 'MC-4: the mini calendar draws seven columns, not one - Demetri found it on the live site' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'mini-calendar-grid - MC-4'; What = 'MC-4: and the grid closes AFTER the loop that fills it' },"""

SUITE_WAS = """    'test_meal_guide3.py'
)"""
SUITE_NOW = """    'test_meal_guide3.py',
    # MC-4, 19 Oct 2026 - the mini calendar is a calendar. The
    # first suite in this project that RENDERS it: every check
    # before this one read its class names, and a layout fault
    # is only visible in the picture.
    'test_mini_grid.py'
)"""

TREE_WAS = """    'test_meal_guide3.py',
]"""
TREE_NOW = """    'test_meal_guide3.py',
    # MC-4, 19 Oct 2026 - the mini calendar is a calendar. Wide from
    # birth: section 4 asks every page in both roots whether any other
    # one has a row of display: contents outside its grid.
    'test_mini_grid.py',
]"""

RD_WAS = """    '.bak_mealguide3',
]"""
RD_NOW = """    '.bak_mealguide3',
    # MC-4, 19 Oct 2026 - the mini calendar draws thirty-five cells in
    # one column, on the live site, because its grid closed before the
    # loop that fills it. Demetri's finding, and no suite in the
    # project had ever rendered the thing.
    '.bak_minigrid',
]"""

WD_WAS = """CONVERTED_N = 110   # MH-3, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 111   # MC-4, 19 Oct 2026 - this round own suite   # (was 110)   # MH-3, 19 Oct 2026 - this round own suite"""


# ============================================================== HELPERS
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
    raise SystemExit('MC-4 REFUSED: %s' % msg)


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
    t_before = t

    # ---------------------------------------------------------------- 0
    if 'THE WEEKS GO INSIDE THE GRID' in t:
        print('MC-4  already applied - the mini calendar is a calendar.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE. A round that fixes nothing is a round
    # whose suite is measuring the weather.
    i = t.find('<div class="mini-calendar-grid">')
    if i < 0:
        refuse('%s has no .mini-calendar-grid' % TPL)
    j = t.find('{% for week in calendar_weeks %}')
    if j < 0:
        refuse('%s has no week loop' % TPL)
    if j < i:
        refuse('%s: the week loop comes before the grid, which is not the '
               'shape this round was written for' % TPL)
    # The grid's own close, found by walking the divs from the opening
    # tag - counted, not guessed, because the headers are divs too.
    depth, k = 0, i
    for m in re.finditer(r'<div\b|</div>', t[i:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            k = i + m.end()
            break
    if k <= i:
        refuse('%s: .mini-calendar-grid never closes' % TPL)
    if k > j:
        refuse('%s: the grid already closes AFTER the week loop, so the '
               'fault this round exists for is not in this tree' % TPL)

    # ---------------------------------------------------------------- 2
    t = swap(t, GRID_WAS, GRID_NOW, '%s (the grid opening)' % TPL)
    t = swap(t, GRID_END_WAS, GRID_END_NOW, '%s (the grid close)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the note on the rule)' % TPL)
    out[pt] = t

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pr = os.path.join(root, TREE)
    out[pr] = swap(read(pr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k2, val in out.items():
        if k2.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k2, root), e.lineno, e.msg))

    # THE GRID NOW CLOSES AFTER THE LOOP, counted the same way the
    # fault was found. This is the whole round and it is checked by
    # walking the divs, not by looking for a string.
    nt = out[pt]
    i2 = nt.find('<div class="mini-calendar-grid">')
    j2 = nt.find('{% endfor %}', nt.find('{% for week in calendar_weeks %}'))
    depth, k2 = 0, i2
    for m in re.finditer(r'<div\b|</div>', nt[i2:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            k2 = i2 + m.end()
            break
    if not (i2 < j2 < k2):
        refuse('%s: the grid still does not contain the week loop - grid '
               'opens at %d, loop ends at %d, grid closes at %d'
               % (TPL, i2, j2, k2))

    # AND THE DIVS BALANCE, by DELTA. One </div> moved and one comment
    # was added; nothing opened and nothing closed. A round that lost a
    # </div> here would hand the rest of the page to the calendar.
    for tag in ('<div', '</div>'):
        if nt.count(tag) != t_before.count(tag):
            refuse('%s: the count of %s moved from %d to %d. This round '
                   'MOVES one close tag and opens nothing.'
                   % (TPL, tag, t_before.count(tag), nt.count(tag)))

    # THE ROW KEEPS display: contents. The fix is to put the row in the
    # grid, NOT to take the rule off - a round that removed it would
    # also break .mini-calendar-week.selected, which paints a whole
    # week, and the week strip is how Demetri navigates.
    if 'display: contents;' not in nt:
        refuse('%s: display: contents is gone from the week row. The fix '
               'is to put the row INSIDE the grid, not to take the rule '
               'away - without it a week cannot be painted as a row.'
               % TPL)

    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))
    for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        if (nt.count(a) - t_before.count(a)
                != nt.count(b) - t_before.count(b)):
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, nt.count(a) - t_before.count(a), a,
                      nt.count(b) - t_before.count(b), b))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MC-4 --check')
        print('  the grid closed at %d and the loop ends at %d - before'
              % (k, j))
        print('  the grid now closes at %d and the loop ends at %d'
              % (k2, j2))
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('MC-4  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_mini_grid.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
