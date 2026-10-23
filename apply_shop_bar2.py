# -*- coding: utf-8 -*-
"""apply_shop_bar2.py - round SB-2, 22 Oct 2026.

THE SHOPPING LIST BAR HAD TWO PRIMARIES ON STEP 2, AND ONE ON A STEP
WHERE NOTHING COULD HAPPEN.

Rendered in Chromium on 22 October, both widths, four states - the
pictures went to Demetri before a line was changed, because the two
questions in them are his and not mine:

    state 1  Generate List [primary]  Help  Back      one primary
    state 2  Done [primary]  Print [primary]  Help  Back   TWO
    state 3  identical to state 1 - Print is hidden again
    state 4  Generate List [primary]  Help  Back
             ... with no step 1 on the page to generate FROM

HE DECIDED: Done keeps the primary, Print becomes a secondary. And
Generate List is hidden when there is nothing it could generate.

WHY STEP 2 HAD TWO. Both buttons were written as .action-primary on
different days by different rounds - SL-2 gave Done the primary when it
built the one-bar, SL-1 had already given Print one when it was the
only new control on the page. Neither round could see the other state.
Nothing failed, because no suite counts primaries within one bar and
3.4 is a written standard rather than an instrumented one.

AND WHY state 4 IS THE SAME FAULT DEMETRI REPORTED IN OCTOBER.

    Print butoon brings up an empty list. Should not appear until
    shopping list has been defined.                  - 3 October

That was Print. This is Generate List, three weeks later, on the page
where no ingredient has a shopping unit: the template gates the whole
two-step flow on {% if ingredients %}, so step 1 is not rendered at all
- and the bar above it still offers to generate from it.

HIDDEN, NOT DISABLED. SL-1's words, and they are still right: a
disabled control still says you may press it and then refuses. The page
already says NOT ON THIS LIST and offers Set base units, which becomes
the only thing on screen to do.

TWO GUARDS, BECAUSE setBar CAN UNDO MARKUP. The template hides the
button; setBar() would reveal it again the moment anything called
setBar(1). Nothing can today - setBar is reached only from the two step
switches, and neither exists in state 4 - but a later round that calls
it on load would quietly undo this one. ALV_CAN_GENERATE is rendered
once by the server and setBar reads it.

NO NEW CONTROL, NO NEW BEHAVIOUR. Print still prints, Done still goes
back to the week you shopped for, and both keep every guard SL-1 gave
them. This round is one class, one conditional attribute and one flag.

Idempotent. Every file backed up to .bak_shopbar2.
"""
import os
import re
import sys

SUFFIX = '.bak_shopbar2'
TPL = os.path.join('pages', 'templates', 'meal_plan_shopping_list.html')
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_shop_bar2.py'
PATCHER = 'apply_shop_bar2.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'SB-2, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# ONE PRIMARY ON STEP 2
# ==========================================================================
PRINT_WAS = """        <button type="button" onclick="printList()" class="btn action-primary"
                id="printBtn" hidden aria-label="Print shopping list">"""

PRINT_NOW = """        {# A SECONDARY - SB-2, 22 Oct 2026. It was an .action-primary,  #}
        {# and so is Done, so step 2 put TWO primaries on one bar.       #}
        {# Neither round could see it: SL-1 gave Print the primary when  #}
        {# it was the only new control on the page, and SL-2 gave Done   #}
        {# one the next day when it built this bar. Nothing failed - no  #}
        {# suite counts primaries WITHIN a bar.                          #}
        {#                                                               #}
        {# DEMETRI CHOSE DONE, 22 October, from the rendered states:     #}
        {# Done is how you finish the flow and it is where his hand      #}
        {# already expects it. Print is a thing you may also want, which #}
        {# is what a secondary is.                                       #}
        <button type="button" onclick="printList()" class="btn action-secondary"
                id="printBtn" hidden aria-label="Print shopping list">"""

# ==========================================================================
# AND NO PRIMARY AT ALL WHEN THERE IS NOTHING TO DO
# ==========================================================================
GEN_WAS = """        <button type="button" onclick="generateShoppingList()" class="btn action-primary" id="genBtn">
            Generate List <i class="fas fa-arrow-right"></i>
        </button>"""

GEN_NOW = """        {# NOT RENDERED WHEN THERE IS NOTHING TO GENERATE - SB-2,        #}
        {# 22 Oct 2026.                                                  #}
        {#                                                               #}
        {# The two-step flow below is inside {% if ingredients %}. When  #}
        {# no ingredient on the plan has a shopping unit, step 1 is not  #}
        {# rendered at all - and this button sat above the empty state   #}
        {# offering to generate a list from it.                          #}
        {#                                                               #}
        {# THE SAME FAULT DEMETRI REPORTED ON 3 OCTOBER, about Print:    #}
        {# "Should not appear until shopping list has been defined."     #}
        {#                                                               #}
        {# NOT RENDERED, NOT hidden, AND NOT disabled. SL-1 chose hidden #}
        {# over disabled because a disabled control still says you may   #}
        {# press it and then refuses - and said in the same breath that  #}
        {# what it really wanted was that "the server never renders a    #}
        {# usable Print for a list that cannot exist". That is available #}
        {# here, because the condition is known before the page is sent. #}
        {#                                                               #}
        {# AND A CONDITIONAL ATTRIBUTE WOULD HAVE BEEN WRONG. The first #}
        {# draft wrote {%% if not ingredients %%} hidden{%% endif %%}     #}
        {# INSIDE the tag. Every instrument in this tree that reads a    #}
        {# template as text - and that is most of them - then sees the   #}
        {# word hidden in the tag and concludes the button always ships  #}
        {# hidden. test_meal_help renders the bar from raw template      #}
        {# text and counted one control fewer; it said so.               #}
        {% if ingredients %}
        <button type="button" onclick="generateShoppingList()" class="btn action-primary" id="genBtn">
            Generate List <i class="fas fa-arrow-right"></i>
        </button>
        {% endif %}"""

# ==========================================================================
# AND setBar MAY NOT UNDO IT
# ==========================================================================
BAR_WAS = """    function setBar(step) {
        var on = {
            genBtn: step === 1,"""

BAR_NOW = """    // WHETHER THERE IS ANYTHING TO GENERATE - SB-2, 22 Oct 2026.
    //
    // Rendered once by the server, from the same `ingredients`
    // condition that decides whether step 1 exists at all.
    //
    // THE CONDITION IS NAMED HERE, NOT WRITTEN. A template tag inside
    // a JavaScript comment is still a template tag: Django does not
    // know that // starts a comment, so the first draft of this block
    // put a live if-tag here and it swallowed the endif belonging to
    // has_missing_conversions nine hundred lines above. The page
    // raised TemplateSyntaxError - 'Invalid block tag: endblock,
    // expected endif' - and it would have done so on Live for anyone
    // whose list had a missing conversion. The suite's render caught
    // it; the dry run and every text gate did not, because as TEXT it
    // is a comment and reads perfectly.
    //
    // setBar reads the flag below so
    // that a call to setBar(1) cannot reveal a button the template
    // deliberately hid.
    //
    // NOTHING CALLS setBar(1) IN THAT STATE TODAY - it is reached only
    // from the two step switches, and neither exists when step 1 was
    // never rendered. This is the second guard, for the later round
    // that calls setBar on load without reading this note. SL-1 wrote
    // three guards for Print on 3 October for the same reason.
    var ALV_CAN_GENERATE = {% if ingredients %}true{% else %}false{% endif %};

    function setBar(step) {
        var on = {
            genBtn: step === 1 && ALV_CAN_GENERATE,"""

# ==========================================================================
# AND SL-2's OWN SUITE NEEDS NOTHING, WHICH IS WORTH WRITING DOWN
# ==========================================================================
# test_shopping_list pins genBtn as always shipping VISIBLE, and this
# round makes it conditional. The first draft of SB-2 therefore edited
# that claim - and it was wrong to.
#
# test_shopping_list reads its page through as_left_by(), which answers
# "the text of this file as the round whose backups end in SUFFIX left
# it": the earliest LATER round's backup, or the file itself. The
# moment this round writes meal_plan_shopping_list.html.bak_shopbar2,
# that suite starts reading the pre-SB-2 text - where genBtn really did
# always ship visible, because that is what SL-2 shipped.
#
# SO THE CLAIM IS STILL TRUE OF THE ROUND THAT MADE IT, and editing it
# would have replaced a true statement about SL-2 with a true statement
# about SB-2 in a file that is not about SB-2. The condition is claimed
# in this round's own suite instead. Measured, not assumed: the edited
# version FAILED, because as_left_by handed the suite the backup and
# the backup has no condition in it.
#
# PG-1 built as_left_by on 18 October for exactly this, and it worked
# on the first round that needed it without anybody having to remember.
def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('SB-2 REFUSED: %s' % msg)


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
        print('SB-2  already applied - one primary, and none with '
              'nothing to do.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE FLOW REALLY IS GATED ON ingredients. This round hangs two
    # things on that fact, so it is asked rather than remembered.
    if '{% if ingredients %}' not in t:
        refuse('%s: the two-step flow is not gated on ingredients, and '
               'this round hides Generate List on exactly that fact'
               % TPL)

    t = swap(t, PRINT_WAS, PRINT_NOW, '%s (Print)' % TPL)
    t = swap(t, GEN_WAS, GEN_NOW, '%s (Generate List)' % TPL)
    t = swap(t, BAR_WAS, BAR_NOW, '%s (setBar)' % TPL)
    out[pt] = t

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_planter_lock.py'
)""", """    'test_planter_lock.py',
    # SB-2, 22 Oct 2026 - one primary on the shopping bar, and none
    # offering to do something there is nothing to do.
    'test_shop_bar2.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/templates/meal_plan_shopping_list.html'; Text = 'ALV_CAN_GENERATE'; What = 'SB-2: step 2 had TWO primaries - Done and Print, written on different days by rounds that could not see each other state. Demetri chose Done. And Generate List is hidden when no ingredient has a shopping unit, because step 1 is not rendered at all then - the same fault he reported about Print on 3 October' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    'test_planter_lock.py',
]""", """    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    'test_planter_lock.py',
    # SB-2, 22 Oct 2026 - one primary on the shopping bar.
    'test_shop_bar2.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    '.bak_planterlock',
]""", """    # LK-1, 22 Oct 2026 - a killed planter leaves a lock behind.
    '.bak_planterlock',
    # SB-2, 22 Oct 2026 - one primary on the shopping bar.
    '.bak_shopbar2',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # SB-2, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nt = out[pt]
    bar = nt[nt.index('<div class="page-action-buttons">'):]
    bar = bar[:bar.index('\n    </div>')]
    # COUNTED ON THE TAGS, NOT ON THE TEXT. The first spelling of this
    # counted the string and got three - because PRINT_NOW's own comment
    # says the word while explaining that Print stopped being one. A
    # gate that cannot tell a class from a sentence about a class is the
    # twelfth instance of "a thing and something that NAMES the thing
    # are not two things".
    # check_gates flags the next three for the same reason, and all
    # three are benign: this round writes the words action-primary,
    # hidden and disabled into COMMENTS that explain which control
    # stopped being a primary, that the button is not rendered rather
    # than hidden, and that it is not disabled either. Every one of the
    # gates is asked of a TAG - the regex matches only from < to the
    # next > - so a sentence about a class cannot satisfy a question
    # about a class. That distinction is the whole reason the first
    # spelling of the count below said three instead of two.
    prim = len([m for m in re.finditer(r'<(?:button|a)\b[^>]*>', bar)
                if 'action-primary' in m.group(0)])
    if prim != 2:
        refuse('%s: the bar carries %d .action-primary control(s). Two '
               'is right - Generate List on step 1 and Done on step 2, '
               'which are never on screen together.' % (TPL, prim))
    # AND THE TWO THAT REMAIN ARE NEVER ON SCREEN AT ONCE.
    for bid in ('genBtn', 'doneBtn'):
        if 'id="%s"' % bid not in bar:
            refuse('%s: %s is not on the bar any more' % (TPL, bid))
    pb = re.search(r'<button[^>]*id="printBtn"[^>]*>', bar)
    if not pb or 'action-secondary' not in pb.group(0):
        refuse('%s: Print is not a secondary, so step 2 still has two '
               'primaries' % TPL)
    gb = re.search(r'<button[^>]*id="genBtn"[^>]*>', bar)
    if not gb:
        refuse('%s: Generate List is not on the bar' % TPL)
    # WRAPPED, NOT ATTRIBUTED. A conditional attribute inside the tag
    # reads as an unconditional `hidden` to every instrument in this
    # tree that parses a template as text, and test_meal_help - which
    # renders the bar from raw template source - counted one control
    # fewer and said so.
    before = bar[:bar.index('id="genBtn"')]
    if '{% if ingredients %}' not in before.rsplit('</button>', 1)[-1]:
        refuse('%s: Generate List is not wrapped in {%% if ingredients '
               '%%}, so it is still rendered when there is nothing to '
               'generate' % TPL)
    if 'hidden' in gb.group(0):
        refuse('%s: Generate List carries a hidden attribute. It is '
               'NOT RENDERED when there is nothing to generate - an '
               'attribute here reads as unconditional to anything that '
               'parses this file as text' % TPL)
    if gb and 'disabled' in gb.group(0):
        refuse('%s: Generate List is DISABLED rather than hidden - a '
               'disabled control still says you may press it and then '
               'refuses, which is SL-1 whole argument' % TPL)
    js = T.code_only_js(nt)
    if 'genBtn: step === 1 && ALV_CAN_GENERATE' not in js:
        refuse('%s: setBar would reveal a button the template hid' % TPL)
    if 'var ALV_CAN_GENERATE = {% if ingredients %}' not in nt:
        refuse('%s: the flag is not asked of the same condition that '
               'decides whether step 1 exists' % TPL)
    # NOTHING ELSE MOVED. Print still prints, Done still leaves.
    if 'onclick="printList()"' not in bar:
        refuse('%s: Print lost its handler' % TPL)
    if 'hasPrintableList' not in js:
        refuse('%s: SL-1 second guard went with the class change' % TPL)

    # THE TEMPLATE MUST STILL BALANCE - SB-2, 22 Oct 2026.
    #
    # Added after this round shipped an unclosed if and nothing noticed
    # until a render. A template tag inside a JavaScript // comment is
    # still a template tag, because Django does not know what // means:
    # one explanatory line in the setBar block put a live {% if %} into
    # the page, it swallowed the {% endif %} of has_missing_conversions
    # nine hundred lines above, and the shopping list raised
    # TemplateSyntaxError for anyone whose list had a missing
    # conversion.
    #
    # EVERY TEXT GATE PASSED IT, because as text it is a comment and
    # reads perfectly. This one counts tags instead, after stripping
    # the comments DJANGO strips - {# #} and no others.
    import re as _re
    _tpl = T.code_only(out[pt])
    _opens = len(_re.findall(r'{%\s*if\b', _tpl))
    _closes = len(_re.findall(r'{%\s*endif\b', _tpl))
    if _opens != _closes:
        refuse('%s: %d {%% if %%} against %d {%% endif %%}. A tag inside '
               'a // comment is still a tag - Django does not know what '
               '// means.' % (TPL, _opens, _closes))
    for _pair in (('for', 'endfor'), ('block', 'endblock')):
        _o = len(_re.findall(r'{%%\s*%s\b' % _pair[0], _tpl))
        _c = len(_re.findall(r'{%%\s*%s\b' % _pair[1], _tpl))
        if _o != _c:
            refuse('%s: %d {%% %s %%} against %d {%% %s %%}'
                   % (TPL, _o, _pair[0], _c, _pair[1]))

    if CHECK:
        print('SB-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        one primary per state, and none with nothing to do')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('SB-2  applied - one primary per state on the shopping bar.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
