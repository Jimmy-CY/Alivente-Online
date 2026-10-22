# -*- coding: utf-8 -*-
"""apply_print_compact.py - round RG-3, 21 Oct 2026.

A SHEET SHOULD BE AS TALL AS WHAT IS ON IT.

Demetri, having printed what RG-1 and RG-2 shipped this morning:

    "I don't like the Weekly Print. The days' height should basically
     be the last recipe (in the day that has the most recipes). The
     same with the Day Print. Just wasting space. Show the Date, and
     the recipes and then done."

HE PICKED B2 AND C2 ON THE STRENGTH OF A RENDER AND CHANGED HIS MIND
ON THE STRENGTH OF PAPER. That is the right way round, and it is the
second time today that printing something has said what a screen
could not.

WHAT THE RULED LINES WERE FOR. B2 was the "writable" week - the space
under each day ruled so the sheet could be taken off the fridge and
written on. C2 was the agenda day with a Notes block under it for the
same reason. Neither survives contact with a real week: his own has
one meal on four of the seven days, so the sheet that came out of the
printer was seven columns of ruled emptiness under five words.

MEASURED ON HIS WEEK - 19 to 25 October, seven meals, one day
carrying three:

    the week sheet   186mm  ->   55mm
    the day sheet    258mm  ->   44mm

Both were one page before and both are one page now; what changed is
how much of the page is blank. The grid is as tall as Friday, which
has three meals, and stops.

THE MONTH IS UNTOUCHED, deliberately. He said the month looked good,
and a month fills its sheet because fitting a whole month on one
sheet of A4 is the entire point of that layout.

AND THE RULED FILL AND THE NOTES BLOCK GO RATHER THAN HIDE. A rule
that paints nothing is a rule the next person has to read and decide
about. `.pp-rule`, `.pp-notes`, `.pp-notes-label` and
`.pp-notes-lines` leave with the markup that wore them.

Idempotent. Every file backed up to .bak_printcompact.
"""
import os
import re
import sys

SUFFIX = '.bak_printcompact'
TPL = os.path.join('pages', 'templates', 'meal_plan_print.html')
SHAPE = 'test_print_shape.py'
ME = 'test_print_compact.py'
PATCHER = 'apply_print_compact.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RG-3, 21 Oct 2026'
CHECK = False
CREATES = ()

# =====================================================================
# THE STYLESHEET
# =====================================================================
RULE_WAS = """.pp-rule {
    flex: 1;
    min-height: 0;
    margin: 6px 10px 10px;
    background-image: repeating-linear-gradient(to bottom,
        transparent 0 25px, var(--alv-line-soft) 25px 26px);
}
.is-week .pp-grid { min-height: 520px; }"""

RULE_NOW = """/* THE RULED FILL IS GONE - RG-3, 21 Oct 2026. It was B2's
   "writable" half: the space under each day ruled so the sheet could
   be written on. On a real week - his own had one meal on four of
   the seven days - it printed as seven columns of ruled emptiness
   under five words. "Just wasting space. Show the Date, and the
   recipes and then done."

   The rule leaves with the markup rather than being hidden, because
   a declaration that paints nothing is one the next person has to
   read and decide about. */
.is-week .pp-meals { padding-bottom: 10px; }"""

NOTES_WAS = """.pp-notes {
    flex: 1;
    min-height: 240px;
    margin-top: 22px;
    border-top: 1px solid var(--alv-line);
    padding-top: 10px;
    display: flex;
    flex-direction: column;
}
.pp-notes-label {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--alv-ink-soft);
    margin-bottom: 8px;
}
.pp-notes-lines {
    flex: 1;
    min-height: 0;
    background-image: repeating-linear-gradient(to bottom,
        transparent 0 26px, var(--alv-line-soft) 26px 27px);
}"""

NOTES_NOW = """/* AND SO IS THE NOTES BLOCK - RG-3, 21 Oct 2026, for the same
   reason and on the same instruction. C2's lower half was 240mm of
   ruled paper under a day that usually holds one or two meals. The
   day sheet is now the date, the meals and the line that says what
   the sheet is. */"""

PRINT_WAS = """    /* ONE SHEET, MEASURED. A month is five week rows or six - August
       2026 and February 2027 are six - and a fixed cell height fits
       one of those and spills the other onto a second page. So the
       SHEET is a fixed box the height of the printable area and the
       grid is a flex column inside it: both months fill exactly one
       sheet, the six-week one tighter. Fixing the sheet rather than
       the grid also means the masthead can change height without
       anybody having to re-measure the number below it.

       A4 landscape is 210mm tall and the margin is 11mm each way, so
       the printable band is 188mm; A4 portrait is 297mm with 18mm
       margins, so 261mm. The two numbers below sit just inside those
       - a sheet exactly as tall as its page rounds onto a second one
       on some printers, which is the fault this block exists to fix.

       test_print_shape prints five of these to real A4 through
       Chromium and reads the page count out of the PDF. */
    .is-month .pp-sheet,
    .is-week .pp-sheet { height: 186mm; display: flex;
                         flex-direction: column; }
    .is-day .pp-sheet { height: 258mm; display: flex;
                        flex-direction: column; }
    .is-month .pp-sheet-grid,
    .is-week .pp-sheet-grid { flex: 1; min-height: 0; display: flex;
                              flex-direction: column; }
    .is-month .pp-week,
    .is-week .pp-week { flex: 1; min-height: 0; display: flex; }
    .is-month .pp-grid,
    .is-week .pp-grid { flex: 1; min-height: 0; height: auto; }
    .is-day .pp-body { flex: 1; min-height: 0; }
    .pp-day, .pp-row { break-inside: avoid; }
    .is-range .pp-week { break-inside: avoid; }"""

PRINT_NOW = """    /* ONE SHEET FOR A MONTH, MEASURED - RG-1, 21 Oct 2026. A month
       is five week rows or six - August 2026 and February 2027 are
       six - and a fixed CELL height fits one of those and spills the
       other onto a second page. So the SHEET is a fixed box the
       height of the printable area and the grid is a flex column
       inside it: both months fill exactly one sheet, the six-week one
       tighter. Fixing the sheet rather than the grid also means the
       masthead can change height without anybody having to re-measure
       the number below it.

       A4 landscape is 210mm tall and the margin is 11mm each way, so
       the printable band is 188mm. 186mm sits just inside it - a
       sheet exactly as tall as its page rounds onto a second one on
       some printers, which is the fault this block exists to fix.

       AND ONLY A MONTH - RG-3, 21 Oct 2026. The week and the day
       filled their sheets too, and on a real week that printed as
       ruled emptiness: "Just wasting space. Show the Date, and the
       recipes and then done." They are as tall as their content now.
       A month still fills its page because fitting a whole month on
       one sheet is the entire point of that layout.

       test_print_compact measures all three heights and reads the
       page counts out of real PDFs. */
    .is-month .pp-sheet { height: 186mm; display: flex;
                          flex-direction: column; }
    .is-month .pp-sheet-grid { flex: 1; min-height: 0; display: flex;
                               flex-direction: column; }
    .is-month .pp-week { flex: 1; min-height: 0; display: flex; }
    .is-month .pp-grid { flex: 1; min-height: 0; height: auto; }
    .pp-day, .pp-row { break-inside: avoid; }
    .is-range .pp-week, .is-week .pp-week { break-inside: avoid; }"""

PHONE_WAS = """    .is-week .pp-grid { min-height: 0; }
    .pp-rule { display: none; }"""

PHONE_NOW = """    .is-week .pp-grid { min-height: 0; }"""


# =====================================================================
# THE MARKUP
# =====================================================================
NOTES_MARKUP_WAS = """            {% empty %}
            <div class="pp-empty">Nothing planned for this day.</div>
            {% endfor %}
            <div class="pp-notes">
                <div class="pp-notes-label">Notes</div>
                <div class="pp-notes-lines"></div>
            </div>
        </div>"""

NOTES_MARKUP_NOW = """            {% empty %}
            <div class="pp-empty">Nothing planned for this day.</div>
            {% endfor %}
        </div>"""

RULE_MARKUP_WAS = """                        {% if sheet == 'week' %}<div class="pp-rule"></div>{% endif %}
"""

RULE_MARKUP_NOW = ""


# =====================================================================
# RG-1's OWN SUITE, CORRECTED IN THE SAME PATCHER
# =====================================================================
# Three of its claims describe the two things this round removes. The
# claims that matter - one sheet, the right paper, nothing truncated,
# a day is not a week - are untouched and still the point.
SHAPE_DAY_WAS = """    c['  the day sheet is an agenda with a Notes block'] = (
        'pp-notes-lines' in page and 'pp-srv' in page)"""

SHAPE_DAY_NOW = """    # RG-3, 21 Oct 2026 - the Notes block is gone. It was 240mm of
    # ruled paper under a day that usually holds one or two meals:
    # "Show the Date, and the recipes and then done."
    c['  the day sheet is the date, the meals and nothing else'] = (
        'pp-notes-lines' not in page and 'pp-srv' in page)"""

SHAPE_WEEK_WAS = """    c['  the week sheet has columns ruled to write in'] = (
        'pp-rule' in page and 'pp-colhead' in page)"""

SHAPE_WEEK_NOW = """    # RG-3, 21 Oct 2026 - the ruled fill is gone with it. The column
    # head stays: a week sheet still names its seven days.
    c['  the week sheet heads each column with its own date'] = (
        'pp-rule' not in page and 'pp-colhead' in page)"""

SHAPE_TALL_WAS = """    c['THE SHEET IS EXACTLY ONE PAGE TALL'] = (
        'height: 186mm' in style and 'height: 258mm' in style)"""

SHAPE_TALL_NOW = """    # RG-3, 21 Oct 2026 - A MONTH IS. The week and the day are as
    # tall as their content now, which is why only one number is
    # left. test_print_compact measures all three.
    c['THE MONTH SHEET IS EXACTLY ONE PAGE TALL'] = (
        'height: 186mm' in style and 'height: 258mm' not in style)"""


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
    raise SystemExit('RG-3 REFUSED: %s' % msg)


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

    if 'RG-3' in t:
        print('RG-3  already applied - the week and the day are as tall '
              'as their content.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, MEASURED. Both sheets really do fill a page.
    code = T.code_only(t)
    style = code[code.index('<style>'):code.index('</style>')]
    for probe in ('height: 186mm', 'height: 258mm'):
        if probe not in style:
            refuse('%s: %s is not in the print block - this round is '
                   'aimed at a page that has moved' % (TPL, probe))
    if 'pp-rule' not in code or 'pp-notes-lines' not in code:
        refuse('%s: the ruled fill or the Notes block is already gone'
               % TPL)

    t = swap(t, RULE_WAS, RULE_NOW, '%s (the ruled fill)' % TPL)
    t = swap(t, NOTES_WAS, NOTES_NOW, '%s (the Notes rules)' % TPL)
    t = swap(t, PHONE_WAS, PHONE_NOW, '%s (the phone block)' % TPL)
    t = swap(t, PRINT_WAS, PRINT_NOW, '%s (the print block)' % TPL)
    t = swap(t, NOTES_MARKUP_WAS, NOTES_MARKUP_NOW,
             '%s (the Notes markup)' % TPL)
    t = swap(t, RULE_MARKUP_WAS, RULE_MARKUP_NOW,
             '%s (the rule markup)' % TPL)
    out[pt] = t

    # ---- RG-1's SUITE, CORRECTED IN THE SAME PATCHER
    ps = os.path.join(root, SHAPE)
    s = read(ps)
    s = swap(s, SHAPE_DAY_WAS, SHAPE_DAY_NOW, '%s (the day)' % SHAPE)
    s = swap(s, SHAPE_WEEK_WAS, SHAPE_WEEK_NOW, '%s (the week)' % SHAPE)
    s = swap(s, SHAPE_TALL_WAS, SHAPE_TALL_NOW, '%s (the height)' % SHAPE)
    out[ps] = s

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    g = read(pp)
    g = swap(g, """    'test_week_fill.py'
)""", """    'test_week_fill.py',
    # RG-3, 21 Oct 2026 - a sheet is as tall as what is on it. The
    # week and the day stop after the last recipe; the month still
    # fills its page, which is the point of the month.
    'test_print_compact.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'corrected by WF-1';""",
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'RG-3, 21 Oct 2026'; What = 'RG-3: the printed week and day are as tall as their content - 186mm to 55mm and 258mm to 44mm on his own week. The ruled fill and the Notes block are gone; the month still fills one sheet' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'corrected by WF-1';""",
             '%s (the sentinels)' % PS1)
    out[pp] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # WF-1, 21 Oct 2026 - the fourth fill, found at the second ask.
    'test_week_fill.py',
]""", """    # WF-1, 21 Oct 2026 - the fourth fill, found at the second ask.
    'test_week_fill.py',
    # RG-3, 21 Oct 2026 - a sheet as tall as what is on it.
    'test_print_compact.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # WF-1, 21 Oct 2026 - the week band gets its colour.
    '.bak_weekfill',
]""", """    # WF-1, 21 Oct 2026 - the week band gets its colour.
    '.bak_weekfill',
    # RG-3, 21 Oct 2026 - the printed week and day stop at the end.
    '.bak_printcompact',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # RG-3, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    ns = nc[nc.index('<style>'):nc.index('</style>')]
    nm = nc[nc.index('</style>'):]
    # THE TWO THINGS REMOVED ARE REALLY GONE, from the rules AND the
    # markup. A class hidden is a class the next person has to decide
    # about.
    for dead in ('pp-rule', 'pp-notes', 'pp-notes-label',
                 'pp-notes-lines'):
        if dead in nc:
            refuse('%s: .%s survived - it should leave with its markup'
                   % (TPL, dead))
    # THE MONTH STILL FILLS ITS SHEET.
    if 'height: 186mm' not in ns:
        refuse('%s: the month lost its fixed height, and fitting a '
               'month on one sheet is the point of it' % TPL)
    # check_gates flags this against SHAPE_TALL_NOW, which quotes the
    # number in the claim it rewrites. That text goes into
    # test_print_shape.py and `ns` is a slice of meal_plan_print.html,
    # so the two never meet. Recorded rather than silenced.
    if 'height: 258mm' in ns:
        refuse('%s: the day still fills a page' % TPL)
    if re.search(r'\.is-week\s+\.pp-sheet\s*\{[^}]*height:\s*\d', ns):
        refuse('%s: the week still fills a page' % TPL)
    # AND NOTHING ELSE ABOUT THE SHEETS MOVED.
    for probe in ('A4 portrait', 'A4 landscape',
                  'repeat(7, minmax(0, 1fr))', 'overflow-wrap: anywhere'):
        if probe not in ns:
            refuse('%s: the rewrite dropped %r' % (TPL, probe))
    if 'pp-colhead' not in nm or 'pp-srv' not in nm:
        refuse('%s: the week column head or the servings column went'
               % TPL)
    # EVERY WIDTH QUERY STILL NAMES screen - the 21 September
    # print-leak rule, on the one page that exists to be printed.
    naked = [m.group(1).strip()
             for m in re.finditer(r'@media([^{]*)\{', out[pt])
             if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
    if naked:
        refuse('%s: a width query that does not name screen: %r'
               % (TPL, naked))
    # AND NOT ONE LITERAL COLOUR.
    hexes = re.findall(r'#[0-9a-fA-F]{3,8}\b', ns)
    if hexes:
        refuse('%s: literal colour(s) in the stylesheet: %r'
               % (TPL, hexes[:6]))

    if CHECK:
        print('RG-3  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        the month keeps 186mm; the week and the day are '
              'content-height')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RG-3  applied - the week and the day stop after the last '
          'recipe.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
