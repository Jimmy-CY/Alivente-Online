"""apply_fi_seg.py - Financial Indicators takes the house switch, and the
last hardcoded accent leaves the page.

    python apply_fi_seg.py --check     dry run, writes nothing
    python apply_fi_seg.py

Run from the repo root. Closes the last presentation item in section 2.C.

THE COMPONENT WAS BUILT BECAUSE OF THIS PAGE AND NEVER APPLIED TO IT.

base's .alv-seg comment says so in as many words:

    "Deferred twice as 'one use does not justify a component' -
     tenant_payment_days and financial_indicators each hand-roll one,
     and this is the third asker."

finance_expense.html was that third asker and got the component. This page,
named in the comment as a reason it exists, kept its Bootstrap .btn-group.
Same shape as the .alv-stat / .ia-kpi round two days ago.

ONE CORRECTION TO THAT COMMENT, and it is left in place rather than quietly
fixed: tenant_payment_days does NOT hand-roll a segmented control. Its only
toggle is .pd-toggle, a per-row expand chevron on aria-expanded with a
rotating icon - a disclosure, not a choice of view. The file contains zero
aria-pressed and zero aria-current. The comment is amended to say what is
actually there, because a component's own note listing an asker that never
existed will send the next reader looking for it.

FOUR CHANGES ON THE PAGE

  1. Budget / Actuals   .btn-group with btn-info / btn-outline-info
                        -> .alv-seg with aria-pressed. These are <a> links
                        that reload with ?basis=, so aria-pressed is the
                        honest attribute: it is a choice of view, and the
                        page tells you which one you are on.

  2. fiCompareBtn       the "Portfolio only" dropdown trigger, btn-outline-
                        info -> .action-secondary. It is not a verb and not
                        the panel's main action; it shows a current value and
                        opens a list.

  3+4. TWO All/None PAIRS THAT DISAGREE WITH EACH OTHER. The same control is
       built twice on this page:

         fiTrendAll / fiTrendNone      outline-info / outline-secondary
         selectAllBtn / selectNoneBtn  btn-info / btn-secondary   (FILLED)

       So in one panel All is a teal outline and in the other it is a filled
       teal block. Both pairs become two matching .action-secondary buttons:
       All and None are equal choices, and neither is what anyone opened the
       panel to do. A filled teal button is the loudest thing this system
       has, and "Select All" has not earned it.

THREE PAGE-LOCAL RULES DIE WITH THEM. .btn-info, .btn-secondary and .btn-sm
serve only the five sites above - verified by scanning the whole file,
including the markup built inside JS template literals.

AND A CLAIM THIS ROUND ALMOST MADE AND CANNOT. A draft of this note said
deleting those rules "takes #0e7c8b out of this page, the last place on this
screen spelling the accent by hand". Counted:

    #0e7c8b   18 uses,  2 of them in the deleted rules
    #0a5e6a    2 uses,  both in the deleted rules
    #6c757d   16 uses,  1 of them in the deleted rules
    #5a6268    1 use,   in the deleted rules
    #545b62    1 use,   in the deleted rules

So #0a5e6a, #5a6268 and #545b62 do leave the page entirely, and the suite
requires it. #0e7c8b does not: sixteen more sit in section borders, badges,
icons and left rules - the page's own palette, spelled out by hand exactly
as the Issues Analysis modal's was before its palette round. That is this
page's next round and it is written down here rather than glossed, because a
push body that overstates what it removed is worse than one that says less.

NOT THIS ROUND: the Issues Analysis modal's three tabs. They were rendered
both ways and left alone deliberately - see the note added to base.

TWO EARLIER SUITES ARE MOVED (section 4b, the scope guard - the seventh and
eighth times in this project). test_print_leaks.py measured "ONLY the guard
changed" live against .bak_leak, which this round's edit invalidates. And
test_button_sweep.py's section 10 pinned two LIVE COUNTS - eight script-built
buttons in four pages, four carrying a LEAVE reason - and this round decides
two of them. The second one is treated differently from the six before it,
and section 4 says why at length: the claim was never about the corpus. It is
about what js_buttons() can see, so it is now ASKED OF THE SCANNER on a
fragment, with the counts kept as a report and the historical eight measured
against the snapshot. A guard asked of the thing it describes does not expire
the next time somebody finishes a page.

AND ONE THING THIS ROUND OPENS. .selection-buttons is built identically on
this page and on finance/vacancy_management.html. Financials' pair is now two
quiet house buttons; vacancy's is still a filled teal block beside a grey one
- the very complaint this round made about the two pairs INSIDE this page.
That is the next round, and it is named here rather than discovered later.

HOUSE RULES: idempotent, .bak_fiseg backups never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import io
import os
import re
import sys
import tokenize

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FI = os.path.join(T, 'finance', 'financial_indicators.html')
for _p in (BASE, FI):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:90]))
    return t.replace(old, new, 1)


def drop_rule(text, selector, what):
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != 1:
        sys.exit('! %s: %r matched %d rule openings, expected 1'
                 % (what, selector, len(hits)))
    m = hits[0]
    i, depth, k = m.start(), 1, m.end()
    while depth and k < len(text):
        if text[k] == '{':
            depth += 1
        elif text[k] == '}':
            depth -= 1
        k += 1
    if depth:
        sys.exit('! %s: unbalanced braces after %r' % (what, selector))
    while k < len(text) and text[k] in '\r\n':
        k += 1
    return text[:i] + text[k:]


def nocomment(src):
    """Python source with its # comments removed.

    A CHECK THAT READS TEXT CATCHES PROSE - the twenty-second time in this
    project, and the second inside a patcher's own self-check. Section 4
    forbids the old literal `len(_all) >= 8 and len(_js) >= 4` from surviving
    in the suite, and the comment that EXPLAINS why it was replaced quotes it
    verbatim. The guard fired on its own explanation. Strip the comments and
    ask the code.
    """
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type != tokenize.COMMENT:
                out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return src
    return '\n'.join(out)


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


# ===========================================================================
# 1. base.html - the component's own note tells the truth about its askers
# ===========================================================================
B_ORIG, B_CRLF, b = load(BASE)
B_DONE = 'AMENDED 2 Sep' in b
if B_DONE:
    print('  base.html already patched')
else:
    b = sub1(b, """/* A segmented control: two or three views of the same screen, one of them
   current. Deferred twice as "one use does not justify a component" -
   tenant_payment_days and financial_indicators each hand-roll one, and this
   is the third asker.""",
             """/* A segmented control: two or three views of the same screen, one of them
   current. Deferred twice as "one use does not justify a component" -
   financial_indicators hand-rolls one out of Bootstrap's .btn-group, and
   finance_expense was the third asker that finally justified building it.

   AMENDED 2 Sep. This note used to name tenant_payment_days as a second
   hand-roller. It is not one: its only toggle is .pd-toggle, a per-row
   expand chevron on aria-expanded with a rotating icon - a disclosure, not
   a choice of view. The file has no aria-pressed and no aria-current. A
   component's note listing an asker that never existed sends the next
   reader looking for it, so the count is corrected rather than left to
   flatter the decision. financial_indicators joined on 2 Sep.

   NOT A TAB BAR, and the difference was measured before it was asserted.
   The Issues Analysis modal has three panel-level tabs - full width, with
   an underline under the current one, sitting directly above the chart they
   control. Rendered as segments they shrink to a third of the row and read
   as a second filter beside the date pickers rather than as part of the
   panel below. A segment here is a PAGE-level choice, worn in an action
   bar; those tabs stay as they are. If a second page ever wants a panel
   tab bar, that is when base gets one - not before.""",
             'base: the .alv-seg note tells the truth')

    _bnc = re.sub(r'/\*.*?\*/', '', b, flags=re.S)
    want('.alv-seg {' in _bnc, 'base: .alv-seg itself was disturbed')
    want(b.count('.alv-seg') >= 8, 'base: the component lost rules')

# ===========================================================================
# 2. financial_indicators.html
# ===========================================================================
F_ORIG, F_CRLF, f = load(FI)
F_DONE = 'alv-seg' in f
if F_DONE:
    print('  financial_indicators.html already patched')
else:
    # ------------------------------------------------- 2a. Budget / Actuals
    # <a> links, not buttons: each reloads with ?basis=. aria-pressed is the
    # honest attribute for "this is the view you are on".
    f = sub1(f, """        <div class="btn-group" role="group" aria-label="Basis">
            <a href="?year={{ selected_year }}&basis=budget"
               class="btn {% if basis == 'budget' %}btn-info{% else %}btn-outline-info{% endif %}">Budget</a>
            <a href="?year={{ selected_year }}&basis=actuals"
               class="btn {% if basis == 'actuals' %}btn-info{% else %}btn-outline-info{% endif %}">Actuals</a>
        </div>""",
             """        <div class="alv-seg" role="group" aria-label="Basis">
            <a href="?year={{ selected_year }}&basis=budget"
               {% if basis == 'budget' %}aria-current="page"{% endif %}>Budget</a>
            <a href="?year={{ selected_year }}&basis=actuals"
               {% if basis == 'actuals' %}aria-current="page"{% endif %}>Actuals</a>
        </div>""", 'FI: Budget / Actuals')

    # ------------------------------------------------------ 2b. the trigger
    f = sub1(f, '<button type="button" id="fiCompareBtn" class="btn btn-outline-info"'
                ' style="min-width:200px; text-align:left;">',
             '<button type="button" id="fiCompareBtn" class="btn action-secondary"'
             ' style="min-width:200px; text-align:left;">',
             'FI: the Compare trigger')

    # ------------------------------------------- 2c/d. the two All/None pairs
    f = sub1(f, '<button type="button" id="fiTrendAll" class="btn btn-sm btn-outline-info" style="flex:1;">All</button>\n'
                '                            <button type="button" id="fiTrendNone" class="btn btn-sm btn-outline-secondary" style="flex:1;">None</button>',
             '<button type="button" id="fiTrendAll" class="btn action-secondary" style="flex:1;">All</button>\n'
             '                            <button type="button" id="fiTrendNone" class="btn action-secondary" style="flex:1;">None</button>',
             'FI: the Compare All/None pair')

    f = sub1(f, '<button class="btn btn-info btn-sm" id="selectAllBtn">Select All</button>\n'
                '                            <button class="btn btn-secondary btn-sm" id="selectNoneBtn">Select None</button>',
             '<button class="btn action-secondary" id="selectAllBtn">Select All</button>\n'
             '                            <button class="btn action-secondary" id="selectNoneBtn">Select None</button>',
             'FI: the Property Selection All/None pair')

    # ------------------------------------------------- 2e. the dead rules
    for _sel in ('.btn-info', '.btn-secondary', '.btn-sm'):
        f = drop_rule(f, _sel, 'FI drop %s' % _sel)
    # Their hover blocks live inside a (hover: hover) wrapper.
    for _old in ("""@media (hover: hover) and (pointer: fine) {
    .btn-info:hover {
        background-color: #0a5e6a;
        border-color: #0a5e6a;
        color: white;
        text-decoration: none;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
}

""", """@media (hover: hover) and (pointer: fine) {
    .btn-secondary:hover {
        background-color: #5a6268;
        border-color: #545b62;
        color: white;
        transform: translateY(-1px);
    }
}

"""):
        f = sub1(f, _old, '', 'FI: a dead hover block')

    f = sub1(f, '/* Button Styles */\n',
             """/* BUTTON STYLES WERE HERE - .btn-info, .btn-secondary and .btn-sm, three
   rules serving five sites, all of them now on the house classes. base's
   .alv-seg carries Budget / Actuals; .action-secondary carries the Compare
   trigger and both All/None pairs.

   Those pairs are why this is worth a note. The SAME control was built twice
   on this page - outline-info / outline-secondary in the Compare panel, and
   filled btn-info / btn-secondary in Property Selection - so in one place
   "All" was a teal outline and in the other a solid teal block. They are two
   equal choices and neither is what anyone opened the panel to do, so both
   pairs are quiet now, and matching.

   Deleting the three rules removed two #0e7c8b, both #0a5e6a, and the two
   grey hovers. It did NOT clear the accent from this page: sixteen more
   #0e7c8b sit in section borders, badges, icons and left rules - the page's
   own palette, spelled by hand exactly as the Issues Analysis modal's was
   before its palette round. That is this page's next round. */
""", 'FI: say what the deleted rules were')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
_nc = re.sub(r'<!--.*?-->', '', _nc, flags=re.S)

for dead in ('btn-info', 'btn-outline-info', 'btn-secondary',
             'btn-outline-secondary', 'btn-sm', 'btn-group'):
    want(not re.search(r'(?<![\w-])%s(?![\w-])' % dead, _nc),
         'FI: %s survives outside a comment' % dead)
# ONLY the literals that were UNIQUE to the deleted rules. #0e7c8b and
# #6c757d have sixteen other homes each on this page, and a check wider than
# its round reports the rest of the file as a defect - third time this week.
for lit in ('#0a5e6a', '#5a6268', '#545b62'):
    want(lit not in _nc, 'FI: the literal %s survives' % lit)
# THE DELTA, on comparable text. The first draft compared a raw grep of the
# original (18) against a comment-stripped count of the result, which are not
# the same measurement. Two literals sat in .btn-info; the rest are the
# page's own palette and stay.
# MEASURED AGAINST THE BACKUP when there is one. On a second run F_ORIG is
# already the patched file, so a delta against it is zero and the check
# reports a correct file as broken - which is exactly what it did.
_before = F_ORIG
_fbak = FI + '.bak_fiseg'
if os.path.exists(_fbak):
    _before = load(_fbak)[0]
_o_nc = re.sub(r'/\*.*?\*/', '', _before.replace('\r\n', '\n'), flags=re.S)
want(_o_nc.count('#0e7c8b') - _nc.count('#0e7c8b') == 2,
     'FI: expected exactly 2 accent literals removed (both in .btn-info), '
     'got %d' % (_o_nc.count('#0e7c8b') - _nc.count('#0e7c8b')))
want(_nc.count('#0e7c8b') >= 15,
     'FI: the page palette was disturbed - %d accent literals left'
     % _nc.count('#0e7c8b'))

want('class="alv-seg"' in _nc, 'FI: the switch did not migrate')
want(_nc.count('aria-current="page"') == 2,
     'FI: expected two aria-current branches, got %d'
     % _nc.count('aria-current="page"'))
# Eight, not five: the page already carried three from the button sweep.
want(_nc.count('class="btn action-secondary"') == 8,
     'FI: expected 3 existing + 5 new house buttons, got %d'
     % _nc.count('class="btn action-secondary"'))
for _id in ('fiCompareBtn', 'fiTrendAll', 'fiTrendNone', 'selectAllBtn',
            'selectNoneBtn'):
    want(_id in _nc, 'FI: the id %s was lost - its script would break' % _id)
want('?year={{ selected_year }}&basis=budget' in _nc
     and '?year={{ selected_year }}&basis=actuals' in _nc,
     'FI: a basis link lost its query string')

# base's component must be intact and its note truthful. The note now names
# tenant_payment_days only to say it is NOT an asker, so the check is that
# the correction is present, not that the name is absent.
# A ONE-LINE marker. The first draft looked for "a disclosure, not a choice
# of view", which wraps across two lines in the comment it was checking, so
# it could never match - and it was also the idempotence marker, so a second
# run would have re-applied and died on its own anchor.
want('AMENDED 2 Sep' in b,
     'base: the corrected .alv-seg note is missing')
want('NOT A TAB BAR' in b,
     'base: the note does not record why the Analysis tabs were left')

# PROSE THAT CONTAINS MARKUP IS MARKUP.
for _name, _text in (('financial_indicators.html', f), ('base.html', b)):
    for _m in re.finditer(r'/\*.*?\*/', _text, re.S):
        want(not re.search(r'</?(?:script|style)\b', _m.group(0)),
             '%s: a CSS comment spells a script or style tag' % _name)

for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'FI: unbalanced braces')

# ===========================================================================
# 3. test_print_leaks.py - SECTION 4b, the SCOPE GUARD, SEVENTH occurrence
# ===========================================================================
# That round asserted, per file, that it changed "ONLY the guard" - measured
# live against .bak_leak. True when written, and true of THAT round. This one
# edits financial_indicators.html, so the comparison now sees this round's
# work and reports it as the print round having done something it did not.
#
# The fix is the one the sticky sweep settled and two rounds have reused: the
# claim is HISTORICAL, so it is measured against the snapshot the LATER round
# leaves. .bak_fiseg is the page as the print round left it. Two fixed points.
# The other checks in that loop stay on the LIVE file, because "no clause
# reaches paper" is a claim about today and must keep being tested.
TP = os.path.join(ROOT, 'test_print_leaks.py')
P_ORIG = P_CRLF = tp = None
P_DONE = True
if not os.path.exists(TP):
    print('  test_print_leaks.py not found - skipping its 4b')
else:
    P_ORIG, P_CRLF, tp = load(TP)
    P_DONE = 'LATER' in tp
    if P_DONE:
        print('  test_print_leaks.py already patched')
    else:
        _anchor = """for rel in TARGETS:
    if BAK[rel] is None:
        continue
    check('%-44s ONLY the guard changed' % rel,
          normalise(SRC[rel]) == normalise(BAK[rel]))"""
        _new = """# MOVED 2 Sep - the SCOPE GUARD kind of 4b, seventh time in this project.
# "ONLY the guard changed" is a claim about what the PRINT round did. It was
# measured live-vs-.bak_leak, which holds exactly until some later round
# legitimately edits one of these files. The Financials segmented-control
# round edits financial_indicators.html.
#
# So for a page a later round owns, the comparison is between TWO SNAPSHOTS -
# .bak_fiseg is that page as the print round left it - which is true for good
# rather than expiring the next time anyone touches it. Every other check in
# this suite stays on the LIVE file: "no clause reaches paper" is a claim
# about today.
LATER = {'finance/financial_indicators.html': '.bak_fiseg'}
for rel in TARGETS:
    if BAK[rel] is None:
        continue
    _later = LATER.get(rel)
    _as_left = SRC[rel]
    if _later:
        _p = os.path.join(T, *rel.split('/')) + _later
        if not os.path.exists(_p):
            check('%-44s a later round left a snapshot' % rel, False, _later)
            continue
        _as_left = read(_p)
    check('%-44s ONLY the guard changed%s'
          % (rel, ' (%s vs .bak_leak - a later round owns the live file)'
             % _later if _later else ''),
          normalise(_as_left) == normalise(BAK[rel]))"""
        if tp.count(_anchor) != 1:
            FAIL.append('test_print_leaks.py: its guard did not match once')
        else:
            tp = tp.replace(_anchor, _new, 1)
            DONE_SUITE = (TP, P_ORIG, P_CRLF,
                          tp.replace('\n', '\r\n') if P_CRLF else tp)
            print('  test_print_leaks.py      scope guard moved to the snapshot')

# ===========================================================================
# 4. test_button_sweep.py - SECTION 4b, the SCOPE GUARD, EIGHTH occurrence,
#    and the first one where the honest fix was NOT to move the claim
# ===========================================================================
# The button sweep's section 10 exists because whole modals are built inside
# JS template literals and a guard that only reads markup reported zero over
# them. It pinned two live counts: EIGHT script-built buttons across FOUR
# pages, FOUR of them carrying a LEAVE reason. Both were true on 28 Aug.
#
# This round decided financial_indicators.html's Select All / Select None.
# They live inside a template literal, they were `btn btn-info btn-sm` and
# `btn btn-secondary btn-sm`, and they are `btn action-secondary` now - so
# the page correctly drops out of a scan that only reports tones base.html
# would own. Measured, before and after, rather than argued:
#
#     as the sweep left it   8 hits / 4 pages / 4 open / 4 with a reason
#     today                  6 hits / 3 pages / 4 open / 2 with a reason
#
# Nothing went blind. A page got finished, which is what the section says it
# wants: "when these are done the number is 4, all of them LEAVE".
#
# SEVEN TIMES THIS PROJECT HAS MOVED A GUARD BY RE-POINTING IT AT A SNAPSHOT,
# and that is right when the claim really is historical. Here it is not. What
# these two checks are FOR is a property of js_buttons() itself -
#
#     * that it can see into a <script> at all,
#     * that it carries a wrapper's LEAVE reason across into a button built
#       inside one,
#
# - and neither of those is a fact about how many pages happen to be undone
# this week. So ASK THE SCANNER, on a two-line fragment, which is the lesson
# CONTROL 4 in this same section already learned about the patcher: it used
# to prove "the sweep does not rewrite scripts" by naming two live pages,
# and stopped meaning anything the moment one of them was decided by hand.
# The corpus counts stay, as a REPORT with a floor, and the historical eight
# is measured where it is still true.
#
# WHY .bak_fiseg IS A FAITHFUL "AS THE SWEEP LEFT IT". The print-leak round
# also touched this file in between, but only to write `screen and ` in front
# of three media queries. It moved no button and no class list, so the
# snapshot this round leaves is the sweep's view of the page for every
# purpose section 10 has.
#
# AND ONE THING THIS ROUND OPENED, written down rather than left to be found.
# .selection-buttons is built identically on TWO pages - here and
# finance/vacancy_management.html. Financials' pair is now two quiet house
# buttons; vacancy's is still a filled teal block beside a grey one. Same
# control, two appearances, which is exactly the complaint this round made
# about the two pairs INSIDE this page. That is the next round. The check
# written for it deliberately passes in both futures - undecided, or decided
# the same way - and fails only on the third: decided differently.
TB = os.path.join(ROOT, 'test_button_sweep.py')
S_ORIG = S_CRLF = tb = None
S_DONE = True
if not os.path.exists(TB):
    print('  test_button_sweep.py not found - skipping its 4b')
else:
    S_ORIG, S_CRLF, tb = load(TB)
    S_DONE = 'ASK THE SCANNER' in tb
    if S_DONE:
        print('  test_button_sweep.py already patched')
    else:
        _a1 = """check('the scan still sees into <script> at all (%d in %d page(s))'
      % (len(_all), len(_js)),
      len(_all) >= 8 and len(_js) >= 4)"""
        _n1 = '''# MOVED 2 Sep - SECTION 4b, the SCOPE GUARD, eighth time in this project and
# the first where moving the claim was the wrong fix. This used to read
# `len(_all) >= 8 and len(_js) >= 4`: a count of live pages, true on 28 Aug.
# The Financials segmented-control round then DECIDED this page's Select All
# / Select None - `btn btn-info btn-sm` inside a template literal, `btn
# action-secondary` now - so it drops out of a scan that reports only tones
# base.html would own. Six in three. Nothing went blind; a page got finished,
# which is the outcome the next check below says it is waiting for.
#
# What this check is FOR is that js_buttons() can see into a <script> at all.
# That is a property of the scanner, not of how many pages are undone this
# week, so ASK THE SCANNER - the lesson CONTROL 4 further down already
# learned about the patcher. The corpus count stays as a report with a floor,
# and the historical eight is measured where it is still true: .bak_fiseg is
# this page as the sweep left it. (The print-leak round edited it in between,
# but only to write `screen and ` in front of three media queries - it moved
# no class list, so the snapshot is faithful for every purpose here.)
#
# _LATER IS THE EXTENSION POINT, one line per page, and that is deliberate.
# The day a round decides vacancy_management's identical pair this control
# will read seven, and the fix is to name that round's snapshot here - NOT to
# lower the number. When the last page is decided there is no state in which
# eight existed, and the control retires with the finding it guards. That is
# the section's own stated goal: "when these are done the number is 4".
_LATER = {'finance/financial_indicators.html': '.bak_fiseg'}


def _as_swept(f):
    """The file as the BUTTON SWEEP left it: the live file, unless a later
       round owns it, in which case that round's snapshot."""
    s = _LATER.get(f)
    if s:
        p = os.path.join(TPL, *f.split('/')) + s
        if os.path.exists(p):
            return load(p)
    return load(os.path.join(TPL, f))


_was = {}
for f in FILES:
    _h = sb.js_buttons(_as_swept(f))
    if _h:
        _was[f] = _h
_was_all = [h for v in _was.values() for h in v]
check('HISTORICAL: eight in four pages, as the sweep left them (%d in %d)'
      % (len(_was_all), len(_was)),
      len(_was_all) == 8 and len(_was) == 4)
check('and the scan still sees into <script> on live pages (%d in %d, %d '
      'still undecided)' % (len(_all), len(_js), len(_open)),
      len(_all) >= 6 and len(_js) >= 3)
# THE INVARIANT, asked of the scanner rather than counted off the corpus, so
# that finishing the last page is a pass and not a failure.
check('CONTROL: .. and would still see one on the day no page has any',
      [h[0] for h in sb.js_buttons(
          '<script>var h = `<div class="page-action-bar">'
          '<button class="btn btn-info">Go</button></div>`;</script>')]
      == ['Go'])
# THE FORWARD HALF. A guard that only ever loosens asserts nothing: say what
# the later round DID, so this cannot be satisfied by the scan going blind.
check('FI dropped out because it was DECIDED, not because the scan lost it',
      'finance/financial_indicators.html' in _was
      and 'finance/financial_indicators.html' not in _js)
_fi_js = '\\n'.join(m.group(1) for m in re.finditer(
    r'<script[^>]*>(.*?)</script>',
    load(os.path.join(TPL, 'finance', 'financial_indicators.html')), re.S))
check('.. its All/None pair carries a house tone INSIDE the script',
      _fi_js.count('class="btn action-secondary"') >= 2
      and 'btn btn-info btn-sm' not in _fi_js)'''
        _a2 = """check('a wrapper already on the LEAVE list carries its reason across',
      len(_all) - len(_open) == 4
      and all(h[5] == 'segmented toggle - colour is state'
              for h in _all if h[5]))"""
        _n2 = '''# MOVED 2 Sep, same round and same reason as the count above. This used to
# read `len(_all) - len(_open) == 4`. Two of those four were this page's
# Select All / Select None, and they are decided; two remain, on
# vacancy_management. The claim worth keeping is that a LEAVE reason CARRIES
# ACROSS into a button built inside a script, and that is asked of the
# scanner below rather than counted off whatever is left undone.
_LEAVE_REASON = 'segmented toggle - colour is state'
_was_open = [h for h in _was_all if not h[5]]
check('HISTORICAL: four of the eight carried a LEAVE reason (%d)'
      % (len(_was_all) - len(_was_open)),
      len(_was_all) - len(_was_open) == 4
      and all(h[5] == _LEAVE_REASON for h in _was_all if h[5]))
check('every reason still reported is the one its wrapper gives',
      all(h[5] == _LEAVE_REASON for h in _all if h[5]))
check('CONTROL: a LEAVE wrapper carries its reason into a script-built '
      'button, whether or not a live page still has one',
      [h[5] for h in sb.js_buttons(
          '<script>var h = `<div class="selection-buttons">'
          '<button class="btn btn-info btn-sm">Select All</button>'
          '</div>`;</script>')] == [_LEAVE_REASON])
# THE DIVERGENCE THIS ROUND OPENED. .selection-buttons is built identically
# on two pages; Financials' pair is now two quiet house buttons and
# vacancy_management's is still a filled teal block beside a grey one - the
# same complaint this round made about the two pairs inside Financials.
# Written as an assertion that holds in BOTH futures, so that doing the work
# is not a test failure. What it forbids is the third: decided differently.
_vac = load(os.path.join(TPL, 'finance', 'vacancy_management.html'))
_vp = re.search(r'<div class="selection-buttons"[^>]*>(.*?)</div>', _vac, re.S)
check("vacancy_management's identical pair is either still undecided or "
      'decided the SAME way as Financials - not a third way',
      _vp is not None
      and (('btn-info' in _vp.group(1) and 'btn-secondary' in _vp.group(1))
           or _vp.group(1).count('btn action-secondary') == 2))'''
        _bad = [n for n, a in (('A', _a1), ('B', _a2)) if tb.count(a) != 1]
        if _bad:
            FAIL.append('test_button_sweep.py: anchor %s did not match once'
                        % ', '.join(_bad))
        else:
            tb = tb.replace(_a1, _n1, 1).replace(_a2, _n2, 1)
            # The suite must still be a parseable module, and the new text
            # must not have re-introduced the literal it replaces.
            try:
                compile(tb, 'test_button_sweep.py', 'exec')
            except SyntaxError as _e:
                FAIL.append('test_button_sweep.py: the patch does not parse '
                            '- %s' % _e)
            _tbc = nocomment(tb)
            want('len(_all) >= 8 and len(_js) >= 4' not in _tbc,
                 'test_button_sweep.py: the old count survives in CODE')
            want('len(_all) - len(_open) == 4' not in _tbc,
                 'test_button_sweep.py: the old LEAVE count survives in CODE')
            # ..and the explanation that quotes them must still be there, or
            # the check above passes on the day somebody deletes the note.
            want('len(_all) >= 8 and len(_js) >= 4' in tb,
                 'test_button_sweep.py: the note no longer says what it '
                 'replaced')
            want(tb.count('_as_swept') == 2,
                 'test_button_sweep.py: _as_swept is not defined and used')
            want(_tbc.count('.bak_fiseg') == 1,
                 'test_button_sweep.py: the snapshot is named %d times in '
                 'CODE, expected once' % _tbc.count('.bak_fiseg'))
            DONE_SWEEP = (TB, S_ORIG, S_CRLF,
                          tb.replace('\n', '\r\n') if S_CRLF else tb)
            print('  test_button_sweep.py     section 10 asks the scanner, '
                  'not the corpus')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-32s %d -> %d bytes'
          % (os.path.basename(p), len(orig), len(out)))
    if CHECK:
        return
    bak = p + '.bak_fiseg'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(BASE, B_ORIG, B_CRLF, b, B_DONE)
save(FI, F_ORIG, F_CRLF, f, F_DONE)
if not P_DONE and tp is not None and 'DONE_SUITE' in dir():
    save(*DONE_SUITE, False)
if not S_DONE and tb is not None and 'DONE_SWEEP' in dir():
    save(*DONE_SWEEP, False)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
