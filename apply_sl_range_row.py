# -*- coding: utf-8 -*-
"""apply_sl_range_row.py - round SH-2, 21 Oct 2026.

THE DATE RANGE WAS A SECOND ACTION BAR, SITTING ABOVE THE FIRST.

Demetri, testing SL-7 on Live:

    "On the Shopping List, for the date range, the date pickers should
     be FAR narrower and fit on one line, with the Show these days
     button. We are using up far too much space at the top of the
     page."

and, a minute later:

    "the date pickers for Shopping List should go under the Generate
     List, Help and Back Button (above Review Ingredients and
     Shopping List)"

HE IS DESCRIBING THE STANDARD. SL-7 wrote the range as

    <form method="get" class="sl-range page-action-buttons">

and placed it ABOVE the real bar. base says two things that forbids:

    "One `.page-action-buttons` row per page."                 (3.4)
    "THE BAR IS THE FIRST THING IN THE FORM. Settled 16 Sep: Save
     sits above the fields, and nothing sits above the bar."   (3.4)

So the page had two bars, and the wrong one came first.

AND A THIRD FAULT NOBODY REPORTED. That form's submit is
`class="btn action-primary"`, while the bar's Generate List is also
an .action-primary - and the two are on screen at the same time, so
the page renders TWO primaries. (Generate List and Done are also both
primaries, but exactly one of them is ever visible, which is the
variant pattern and is fine.) "Show these days" re-asks the page for
a different range; the page's verb is still Generate List. It becomes
a secondary.

WHAT IT LOOKS LIKE NOW. One line: From, a date, To, a date, the
button - with the inputs sized to a date instead of stretched by
form-control's width:100%. On a phone it wraps to two lines rather
than stretching, because a date input at 390px has no business being
340px wide.

IT STILL PRINTS NOTHING. .sl-range stays in SL-1's @media print hide
list; a shopping list on the fridge does not need a form on it.

Idempotent. Every file backed up to .bak_slrangerow.
"""
import os
import re
import sys

SUFFIX = '.bak_slrangerow'
TPL = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
ME = 'test_sl_range_row.py'
PATCHER = 'apply_sl_range_row.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'SH-2, 21 Oct 2026'
CHECK = False
CREATES = ()

# ---- THE FORM COMES OUT OF WHERE IT WAS
FORM_WAS = """{# A GET, AND THE SAME TWO PARAMETERS THE SERVER HAS TAKEN SINCE    #}
{# MN-1. No new endpoint, no new aggregation path - this re-asks    #}
{# the page it is on.                                               #}
{#                                                                  #}
{# IT PRINTS NOTHING. SL-1 hides .page-action-buttons on paper and  #}
{# this belongs with them: a shopping list on the fridge does not   #}
{# need a form on it.                                                #}
<form method="get" action="" class="sl-range page-action-buttons">
    <label class="sl-range-label" for="slFrom">From</label>
    <input type="date" id="slFrom" name="from" class="form-control"
           value="{{ start|date:'Y-m-d' }}">
    <label class="sl-range-label" for="slTo">To</label>
    <input type="date" id="slTo" name="to" class="form-control"
           value="{{ end|date:'Y-m-d' }}">
    <button type="submit" class="btn action-primary">Show these days</button>
</form>
<div class="page-action-buttons">"""

FORM_NOW = """<div class="page-action-buttons">"""

# ---- AND GOES IN UNDER THE BAR, which is where the standard puts
# anything that is not the bar. The anchor is the close of the bar's
# own div, immediately before the step indicator.
AFTER_WAS = """    <div class="step-indicator">"""

AFTER_NOW = """    {# UNDER THE BAR - SH-2, 21 Oct 2026.                              #}
    {#                                                                  #}
    {# SL-7 put this ABOVE the action bar and gave it the bar's own     #}
    {# class, so the page had two .page-action-buttons rows and the     #}
    {# wrong one came first. base 3.4 forbids both: one bar per page,   #}
    {# and nothing sits above it. Demetri reported it as wasted space   #}
    {# at the top of the page, which is what a second bar looks like.   #}
    {#                                                                  #}
    {# A GET, AND THE SAME TWO PARAMETERS THE SERVER HAS TAKEN SINCE    #}
    {# MN-1. No new endpoint, no new aggregation path - this re-asks    #}
    {# the page it is on.                                               #}
    {#                                                                  #}
    {# IT PRINTS NOTHING. SL-1 hides .page-action-buttons on paper and  #}
    {# this belongs with them: a shopping list on the fridge does not   #}
    {# need a form on it.                                                #}
    <form method="get" action="" class="sl-range">
        {# EACH LABEL IS WELDED TO ITS INPUT. Loose in a wrapping flex #}
        {# row they are five independent children, and at 390px the    #}
        {# row broke as "From [date] To" / "[date]" - the To label      #}
        {# orphaned at the end of a line with its own field underneath. #}
        <span class="sl-range-pair">
            <label class="sl-range-label" for="slFrom">From</label>
            <input type="date" id="slFrom" name="from" class="sl-range-date"
                   value="{{ start|date:'Y-m-d' }}">
        </span>
        <span class="sl-range-pair">
            <label class="sl-range-label" for="slTo">To</label>
            <input type="date" id="slTo" name="to" class="sl-range-date"
                   value="{{ end|date:'Y-m-d' }}">
        </span>
        {# A SECONDARY. The page's verb is Generate List, and that is  #}
        {# on screen at the same time as this - so an .action-primary  #}
        {# here is a second primary, which 3.4 forbids outright.       #}
        <button type="submit" class="btn action-secondary">Show these days</button>
    </form>

    <div class="step-indicator">"""

# ---- AND IT GETS A RULE OF ITS OWN, because it had none: the form
# was laid out entirely by the bar class it had borrowed, so taking
# that away leaves it with nothing.
CSS_WAS = """/* Step Navigation */
.step-indicator {"""

CSS_NOW = """/* THE RANGE ROW - SH-2, 21 Oct 2026.
   This had NO rule at all. It wore .page-action-buttons and was laid
   out by it, which is the whole reason it looked like a bar: it was
   being painted as one. Now it is what it is - a compact filter.

   WIDTH: AUTO ON THE DATES. They were .form-control, which is
   width:100%, so two date inputs and a button stretched across the
   page and ate the top of it. A date input sized to a date is about
   150px; the browser decides, and `width: auto` lets it.

   44px, because that is what 3.4 promises a control on a phone and
   what ALV FILTER FIELD gives every other filter in the system.
   --alv-line for the border, which is the colour every field in the
   system uses. */
.sl-range {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 18px;
}
.sl-range-pair {
    display: inline-flex;
    align-items: center;
    gap: 7px;
}
.sl-range-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    margin: 0;
    letter-spacing: 0.02em;
}
.sl-range-date {
    width: auto;
    height: 44px;
    padding: 0 10px;
    font-size: 14px;
    color: var(--alv-ink);
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
}
.sl-range-date:focus {
    outline: 2px solid var(--alv-accent);
    outline-offset: -1px;
    border-color: var(--alv-accent);
}
.sl-range .btn {
    height: 44px;
}

/* A PHONE WRAPS IT, it does not stretch it. Two dates and a button
   on one 390px line would give each about 110px; the row breaks
   after the second date instead and the button takes its own line. */
/* A PHONE TAKES TWO LINES, NOT THREE. The pairs share the first -
   half each - and the button sits on the second at its own width,
   because a secondary stretched across the screen reads as a verb. */
@media screen and (max-width: 767px) {
    .sl-range { gap: 6px; }
    .sl-range-pair { flex: 1 1 calc(50% - 3px); min-width: 0; }
    .sl-range-pair .sl-range-date { flex: 1 1 auto; min-width: 0; }
    .sl-range .btn { flex: 0 0 auto; }
}

/* Step Navigation */
.step-indicator {"""


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
    raise SystemExit('SH-2 REFUSED: %s' % msg)


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


BARS = re.compile(r'<(?:div|form)\b[^>]*class="[^"]*\bpage-action-buttons\b')


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'UNDER THE BAR - SH-2' in t:
        print('SH-2  already applied - the range sits under the bar.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)

    # ---- THE FINDING, MEASURED. Two bars, and the form is the first.
    bars = [m.start() for m in BARS.finditer(code)]
    if len(bars) != 2:
        refuse('%s: %d element(s) wear page-action-buttons, expected the '
               '2 this round merges' % (TPL, len(bars)))
    first = code[bars[0]:bars[0] + 120]
    if '<form' not in first:
        refuse('%s: the first bar is not the range form, so this round '
               'is aimed at the wrong page' % TPL)

    t = swap(t, FORM_WAS, FORM_NOW, '%s (lifting the form)' % TPL)
    t = swap(t, AFTER_WAS, AFTER_NOW, '%s (placing it under the bar)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (its own rule)' % TPL)
    out[pt] = t

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, """    'test_week_band.py'
)""", """    'test_week_band.py',
    # SH-2, 21 Oct 2026 - the shopping list had two action bars and
    # the wrong one came first.
    'test_sl_range_row.py'
)""", '%s (the suites)' % PS1)
    s = swap(s,
             """    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEK OWNS THE EDGE';""",
             """    @{ File = 'pages/templates/meal_plan_shopping_list.html'; Text = 'UNDER THE BAR - SH-2'; What = 'SH-2: the from/to range sits under the action bar and is a compact row rather than a second .page-action-buttons above it - the page had two bars, which 3.4 forbids, and two visible primaries' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WEEK OWNS THE EDGE';""",
             '%s (the sentinels)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # WT-1, 21 Oct 2026 - a row and the pills on it, told apart.
    'test_week_band.py',
]""", """    # WT-1, 21 Oct 2026 - a row and the pills on it, told apart.
    'test_week_band.py',
    # SH-2, 21 Oct 2026 - one bar per page, and the range under it.
    'test_sl_range_row.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # WT-1, 21 Oct 2026 - the week owns the edge, the meal the fill.
    '.bak_weekband',
]""", """    # WT-1, 21 Oct 2026 - the week owns the edge, the meal the fill.
    '.bak_weekband',
    # SH-2, 21 Oct 2026 - the range row stops being a second bar.
    '.bak_slrangerow',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # SH-2, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nc = T.code_only(out[pt])
    nbars = [m.start() for m in BARS.finditer(nc)]
    if len(nbars) != 1:
        refuse('%s: %d page-action-buttons after this round, expected 1'
               % (TPL, len(nbars)))
    # THE RANGE IS BELOW THE BAR, by position in the document.
    if 'class="sl-range"' not in nc:
        refuse('%s: the range form is gone entirely' % TPL)
    if nc.index('class="sl-range"') < nbars[0]:
        refuse('%s: the range still sits ABOVE the bar' % TPL)
    # AND ABOVE THE STEPS, which is where he put it.
    if 'step-indicator' in nc and \
            nc.index('class="sl-range"') > nc.index('class="step-indicator"'):
        refuse('%s: the range sits below the step indicator' % TPL)
    # THE RANGE BUTTON IS NOT A PRIMARY.
    #
    # SCOPED TO THE FORM, not to the page. The first draft of this
    # gate counted every .action-primary in the file and refused at
    # three - but two of those are saveConversionsBtn and
    # emailSendBtn, which are the primaries of a PANEL and a DIALOG.
    # Every dialog in this application has a primary and should.
    # base 3.4's sentence is about the bar: "One .page-action-buttons
    # row per page. Exactly one .action-primary - the page's verb."
    # FROM THE TAG, NOT FROM THE ATTRIBUTE. A window opened at
    # class="sl-range" starts PAST method="get", which sits earlier in
    # the same tag - so a check for it reads as missing on a form that
    # has it. Open the window where the element opens.
    _i = nc.rindex('<form', 0, nc.index('class="sl-range"'))
    rng = nc[_i:nc.index('</form>', _i) + 7]
    if 'action-primary' in rng:
        refuse('%s: the range button is still a primary, and Generate '
               'List is on screen beside it' % TPL)
    if 'action-secondary' not in rng:
        refuse('%s: the range button wears no house role at all' % TPL)
    # AND THE BAR DID NOT GET WORSE. Its own primaries are a variant
    # set that setBar() switches at runtime - SL-1 and SL-2's design,
    # not this round's to re-cut - so the claim is that the count is
    # unchanged, not that it is one.
    def bar_primaries(src):
        i = src.index('class="page-action-buttons"')
        j = src.index('</div>', src.index('doneBtn', i))
        return src[i:j].count('action-primary')
    if bar_primaries(nc) != bar_primaries(code):
        refuse('%s: the bar held %d primaries and now holds %d'
               % (TPL, bar_primaries(code), bar_primaries(nc)))
    # THE FORM STILL WORKS: a GET carrying both names.
    for probe in ('method="get"', 'name="from"', 'name="to"',
                  'type="submit"'):
        if probe not in rng:
            refuse('%s: the range form lost %s' % (TPL, probe))
    # AND IT STILL PRINTS NOTHING.
    pblock = nc[nc.index('@media print'):] if '@media print' in nc else ''
    if '.sl-range' not in pblock:
        refuse('%s: .sl-range is no longer hidden on paper' % TPL)
    # THE DATES ARE SIZED TO A DATE.
    if 'width: auto' not in nc:
        refuse('%s: the date inputs are still stretched' % TPL)

    if CHECK:
        print('SH-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        bars on the page: %d -> %d' % (len(bars), len(nbars)))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('SH-2  applied - one bar, and the range under it.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
