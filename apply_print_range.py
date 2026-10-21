# -*- coding: utf-8 -*-
"""apply_print_range.py - round RG-2, 21 Oct 2026.

THE PRINTED PLAN COULD NOT BE ASKED FOR A RANGE, AND THE SECOND
PRESS LOOKED LIKE A MISTAKE.

Demetri, 21 October, two items of the eleven:

    "Why do we need to Press 'Print' twice. It is very inefficient."

    "Print Date Range needs to be included (similar to the Shopping
     List)"

THE TWO ARE ONE PAGE'S PROBLEM. The print page already reads ?from=
and ?to= - PP-1 built it that way on purpose, so that the planner
could hand it SL-7's range - but there was no way to CHANGE them once
you were there. The only route to a different fortnight was back to
the planner, onto a different view, and Print again.

AND THE SECOND PRESS. He was offered three answers and chose: "Keep
two steps, make the second obvious." The second step is the browser's
own print dialog, and it cannot be skipped - window.print() IS the
dialog, and a page that printed the moment it loaded would be a page
nobody could change the dates on, which is the other half of this
round. So the page says what it is and what the button does, in one
line, instead of looking like a page that failed to print.

THE SAME ROW THE SHOPPING LIST GREW THIS MORNING. SH-2 put From, To
and a button on one 44px line there, after he said the pickers were
"using up far too much space at the top of the page". This is that
row, on this page - and it is written out again rather than reused,
because .sl-range is DEFINED IN meal_plan_shopping_list.html and a
class is not a style. That is PP-1's .calendar-container mistake, and
it cost a round.

A SECONDARY, NOT A SECOND PRIMARY. The page's verb is Print, and it
is on screen at the same time as this button. 3.4 allows one.

Idempotent. Every file backed up to .bak_printrange.
"""
import os
import re
import sys

SUFFIX = '.bak_printrange'
TPL = os.path.join('pages', 'templates', 'meal_plan_print.html')
ME = 'test_print_range.py'
PATCHER = 'apply_print_range.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RG-2, 21 Oct 2026'
CHECK = False
CREATES = ()


CSS_WAS = """/* AND screen, NOT a bare max-width - a clause naming no media type"""

CSS_NOW = '''/* ---- THE RANGE, AND THE SECOND STEP -------------------------------
   SH-2 put From, To and one button on a single 44px line on the
   shopping list this morning, after Demetri said the pickers were
   "using up far too much space at the top of the page". This is that
   row again, on the other page that takes the same two dates.

   WRITTEN OUT, NOT REUSED. .sl-range is defined in
   meal_plan_shopping_list.html, not in base, so on this page it is a
   name with no rules behind it. That is exactly the mistake PP-1
   made with .calendar-container and it cost a round; the geometry is
   copied deliberately, the class name is this page's own.

   44px, because that is what 3.4 promises a control on a phone, and
   --alv-line for the border, which is what every field in the system
   wears. */
.pp-range {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}
.pp-range-pair {
    display: inline-flex;
    align-items: center;
    gap: 7px;
}
.pp-range-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    margin: 0;
    letter-spacing: 0.02em;
}
.pp-range-date {
    width: auto;
    height: 44px;
    padding: 0 10px;
    font-size: 14px;
    color: var(--alv-ink);
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
}
.pp-range-date:focus {
    outline: 2px solid var(--alv-accent);
    outline-offset: -1px;
    border-color: var(--alv-accent);
}
.pp-range .btn { height: 44px; }

/* THE SECOND STEP, SAID OUT LOUD. He asked why Print has to be
   pressed twice and chose "keep two steps, make the second obvious".
   window.print() IS the browser's dialog - there is no third thing
   this page could do instead - so what was missing was not a step
   but a sentence. */
.pp-hint {
    font-size: 12.5px;
    color: var(--alv-ink-soft);
    background: var(--alv-surface);
    border: 1px solid var(--alv-line);
    border-left: 3px solid var(--alv-accent);
    border-radius: var(--alv-radius-sm);
    padding: 9px 12px;
    margin-bottom: 18px;
}
.pp-hint i { color: var(--alv-accent); margin-right: 5px; }
.pp-hint strong { color: var(--alv-ink); }

/* AND screen, NOT a bare max-width - a clause naming no media type'''

PHONE_WAS = """@media screen and (max-width: 767px) {
    .pp-page { padding: 8px; }"""

PHONE_NOW = """@media screen and (max-width: 767px) {
    .pp-page { padding: 8px; }
    /* TWO LINES, NOT THREE - SH-2's measurement, 21 Oct 2026. The
       pairs take half the first line each and the button sits on the
       second at its own width, because a secondary stretched across
       the screen reads as a verb. */
    .pp-range { gap: 6px; }
    .pp-range-pair { flex: 1 1 calc(50% - 3px); min-width: 0; }
    .pp-range-pair .pp-range-date { flex: 1 1 auto; min-width: 0; }
    .pp-range .btn { flex: 0 0 auto; }"""

BODY_WAS = """    <div class="pp-sheet">
"""

BODY_NOW = '''    {# THE RANGE - RG-2, 21 Oct 2026.                                #}
    {#                                                               #}
    {# "Print Date Range needs to be included (similar to the        #}
    {#  Shopping List)". The view has read ?from= and ?to= since     #}
    {# PP-1; there was simply no way to change them once you were    #}
    {# here, so a different fortnight meant going back to the        #}
    {# planner, onto another view, and pressing Print again.         #}
    {#                                                               #}
    {# UNDER THE BAR, which is where SH-2 put the shopping list's -  #}
    {# "the date pickers should go under the Generate List, Help and #}
    {# Back Button". base 3.4: nothing sits above the bar.           #}
    {#                                                               #}
    {# IT PRINTS NOTHING. .pp-noprint, with the bar.                 #}
    <form method="get" action="" class="pp-range pp-noprint">
        {# EACH LABEL WELDED TO ITS INPUT - SH-2, 21 Oct 2026. Loose #}
        {# in a wrapping flex row they are five independent children #}
        {# and at 390px the row broke as "From [date] To" / "[date]",#}
        {# with the To label orphaned at the end of a line.          #}
        <span class="pp-range-pair">
            <label class="pp-range-label" for="ppFrom">From</label>
            <input type="date" id="ppFrom" name="from" class="pp-range-date"
                   value="{{ start|date:'Y-m-d' }}">
        </span>
        <span class="pp-range-pair">
            <label class="pp-range-label" for="ppTo">To</label>
            <input type="date" id="ppTo" name="to" class="pp-range-date"
                   value="{{ end|date:'Y-m-d' }}">
        </span>
        {# A SECONDARY. The page's verb is Print and it is on screen #}
        {# at the same time as this, so a primary here would be the  #}
        {# second one 3.4 forbids.                                   #}
        <button type="submit" class="btn action-secondary">Show these days</button>
    </form>

    {# THE SECOND STEP, SAID OUT LOUD - RG-2, 21 Oct 2026.           #}
    {# "Why do we need to Press Print twice. It is very              #}
    {#  inefficient." - and his answer to the three options was      #}
    {# "Keep two steps, make the second obvious". window.print() IS  #}
    {# the browser's own dialog; there is no third thing this page   #}
    {# could do instead, and a page that printed itself on load      #}
    {# would be a page you could not change the dates on. So what    #}
    {# was missing was not a step - it was a sentence.               #}
    <p class="pp-hint pp-noprint">
        <i class="fas fa-print"></i>
        <strong>Step 2 of 2.</strong> This sheet is laid out and ready.
        Press <strong>Print</strong> above to open your printer dialog{% if sheet != 'range' %} - it is one A4 sheet, {% if sheet == 'day' %}portrait{% else %}landscape{% endif %}{% endif %}.
    </p>

    <div class="pp-sheet">
'''


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
    raise SystemExit('RG-2 REFUSED: %s' % msg)


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

    if 'THE RANGE - RG-2' in t:
        print('RG-2  already applied - the print page takes a range.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)

    # ---- THE FINDING, MEASURED. The page reads two dates and offers
    # no way to type them.
    # (Idempotency is the marker above, not a class name: check_gates
    # is right that a gate must not forbid the text its own round
    # writes, and `pp-range` is text this round writes.)
    if '<form' in code:
        refuse('%s: this page already carries a form, and this round '
               'assumes it is the first' % TPL)
    if 'is-{{ sheet }}' not in t:
        refuse('%s: RG-1 has not been applied - this round sits on its '
               'page' % TPL)

    t = swap(t, CSS_WAS, CSS_NOW, '%s (the range CSS)' % TPL)
    t = swap(t, PHONE_WAS, PHONE_NOW, '%s (the phone row)' % TPL)
    t = swap(t, BODY_WAS, BODY_NOW, '%s (the range row)' % TPL)
    out[pt] = t

    # ---- THE ONE CENSUS THIS ROUND MOVES, measured by running the
    # suite against the applied tree rather than estimated.
    pc = os.path.join(root, 'test_pair_contrast.py')
    out[pc] = swap(read(pc), 'EXPECT_PAIRS = 724   # RG-1, 21 Oct 2026',
                   'EXPECT_PAIRS = 726   # RG-2, 21 Oct 2026 - two '
                   'more rules set a fill and an ink together: the '
                   'date field, which wears the paper token on the '
                   'ink one like every other field in the system, and '
                   'the line explaining the second Print press, which '
                   'sits on the surface wash.   # (was 724)   '
                   '# RG-1, 21 Oct 2026',
                   'test_pair_contrast.py (the census)')

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_print_shape.py'
)""", """    'test_print_shape.py',
    # RG-2, 21 Oct 2026 - the printed plan takes a range of its own,
    # and says what the second Print press is for.
    'test_print_range.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'is-{{ sheet }}';""",
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'THE RANGE - RG-2'; What = 'RG-2: From and To on the printable plan, on one 44px line like the shopping list - and a line saying what the second Print press does, which is the answer he chose to "why do we press Print twice"' },
    @{ File = 'pages/templates/meal_plan_print.html'; Text = 'is-{{ sheet }}';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # RG-1, 21 Oct 2026 - a printed day that was a week.
    'test_print_shape.py',
]""", """    # RG-1, 21 Oct 2026 - a printed day that was a week.
    'test_print_shape.py',
    # RG-2, 21 Oct 2026 - the range, and the second press explained.
    'test_print_range.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # RG-1, 21 Oct 2026 - four sheets, and a month on one of them.
    '.bak_printshape',
]""", """    # RG-1, 21 Oct 2026 - four sheets, and a month on one of them.
    '.bak_printshape',
    # RG-2, 21 Oct 2026 - From, To, and what the second press is for.
    '.bak_printrange',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # RG-2, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    # ONE BAR. BA-1 taught the detector to see a <form> this morning,
    # and SL-7 is the reason it had to: a range written as
    # <form class="sl-range page-action-buttons"> gave that page two
    # bars and nothing could see the second.
    bars = re.findall(r'<(?:div|form)[^>]*class="[^"]*'
                      r'\bpage-action-buttons\b[^"]*"[^>]*>', nc)
    if len(bars) != 1:
        refuse('%s: %d action bars on the page, expected 1 - the range '
               'form must not wear page-action-buttons' % (TPL, len(bars)))
    # ONE PRIMARY, and it is Print.
    roles = re.findall(r'class="btn (action-[a-z]+)"', nc)
    if roles.count('action-primary') != 1:
        refuse('%s: %d primaries, and 3.4 allows one'
               % (TPL, roles.count('action-primary')))
    if roles != ['action-primary', 'action-back', 'action-secondary']:
        refuse('%s: the controls read %r' % (TPL, roles))
    # NO CONTROL SITS ABOVE THE BAR - base 3.4, "THE BAR IS THE FIRST
    # THING IN THE FORM".
    #
    # THE PAGE'S TITLE DOES, and must: test_bar_top reads all 151
    # templates and asserts that none of them puts its action bar
    # above its heading. The two rules are about different things -
    # one about where the verbs are, one about where the name is -
    # and the first spelling of this gate confused them.
    #
    # SLICED FROM THE MARKUP. The print block names
    # .page-action-buttons to hide it, which is above everything in
    # the body, so a gate that indexes the whole file measures a
    # region that runs backwards and passes on an empty string.
    mk = nc[nc.index('</style>'):]
    before = mk[mk.index('<div class="pp-page'):
                mk.index('page-action-buttons')]
    if re.search(r'<(?:form|input|button|table)\b', before):
        refuse('%s: a control sits above the bar' % TPL)
    if 'page-title-h2' not in before:
        refuse('%s: the page title is not above the bar - test_bar_top '
               'reads every template in the tree for exactly this' % TPL)
    # AND THE ROW IS ABOVE THE SHEET, NOT INSIDE IT.
    if mk.index('class="pp-range') > mk.index('class="pp-sheet"'):
        refuse('%s: the range row is inside the sheet, so it would be '
               'printed' % TPL)
    # THE TWO DATES ARE THE TWO THE VIEW READS.
    names = re.findall(r'<input[^>]*name="(\w+)"', nc)
    if sorted(names) != ['from', 'to']:
        refuse('%s: the form posts %r, and the view reads from and to'
               % (TPL, names))
    if 'method="get"' not in nc[nc.index('<form'):nc.index('<form') + 90]:
        refuse('%s: the range form is not a GET, so the dates would '
               'not survive a refresh or a bookmark' % TPL)
    # IT PRINTS NOTHING.
    for cls in ('pp-range', 'pp-hint'):
        m = re.search(r'class="%s[^"]*"' % cls, nc)
        if not m or 'pp-noprint' not in m.group(0):
            refuse('%s: .%s would be printed' % (TPL, cls))
        if not re.search(r'\.%s[\s,.:{>+~\[]' % cls, nc):
            refuse('%s: .%s is worn and never styled' % (TPL, cls))
    # EVERY WIDTH QUERY STILL NAMES screen.
    naked = [m.group(1).strip()
             for m in re.finditer(r'@media([^{]*)\{', out[pt])
             if 'max-width' in m.group(1) and 'screen' not in m.group(1)]
    if naked:
        refuse('%s: a width query that does not name screen: %r'
               % (TPL, naked))
    # AND NOT ONE LITERAL COLOUR ARRIVED WITH IT.
    style = nc[nc.index('<style>'):nc.index('</style>')]
    hexes = re.findall(r'#[0-9a-fA-F]{3,8}\b', style)
    if hexes:
        refuse('%s: literal colour(s) in the stylesheet: %r'
               % (TPL, hexes[:6]))

    if CHECK:
        print('RG-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        bars %d, controls %s' % (len(bars), roles))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RG-2  applied - the printed plan takes a range.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
