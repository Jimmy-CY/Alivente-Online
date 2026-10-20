# -*- coding: utf-8 -*-
"""apply_date_bar.py - round DB-1, 20 Oct 2026.

THE RESPONSIVE BLOCK THAT NEVER CLOSED.

Demetri, testing push 2 on production, at about 1900 CSS pixels:

    "The October 2026 and the arrows still looks a mess."
    "The daily looks good, but the arrows and date on top are a mess."

MEASURED, NOT READ. The same page at two widths, same markup:

                  1200px                     1900px
    arrow         36x36, panel grey, r6      20x21, 2px OUTSET black
    Today         67x36, in the panel        69x19
    title         903x23, 20px/600, centred  138x17, 16px/400, left

`2px outset black` on `#efefef` is the browser's DEFAULT BUTTON. Above
1200px no rule reaches the bar at all.

THE CAUSE IS ONE MISSING BRACE, AND IT IS OLD.

    /* ==================== RESPONSIVE ==================== */
    @media screen and (max-width: 1200px) {
        .calendar-layout {
            grid-template-columns: 1fr;
        }
                                          <-- nothing closes it
    @media screen and (max-width: 768px) {

It opens, holds ONE rule, and never closes, so every rule after it to
the end of the <style> is nested inside it - the 768px blocks included,
which is why they read `1200px AND 768px` in the browser.

DATED ACROSS THE BACKUPS, because "did push 2 do this" is a fair
question and the answer is no:

    .bak_mealweek      722 lines,  54 rules swallowed
    .bak_monthbar     2198 lines,  77     (pre-MB-2)
    live              2471 lines,  88

It has been there for weeks and has grown every time a round appended
CSS. MB-2 did not break the date bar; it wrote the date bar into a
region that was already dead above 1200px, and so did everything else
down there.

> A RULE'S TEXT BEING PRESENT SAYS NOTHING ABOUT WHETHER IT APPLIES.
> MB-2's suite asked whether the declarations were in the file. They
> were. No suite in this system had ever asked what media a rule ends
> up in, which is why eighty-eight of them could go dark unnoticed.

WHAT THIS ROUND DOES: deletes the wrapper rather than closing it.

The one rule inside is `.calendar-layout { grid-template-columns: 1fr }`
- a leftover from when the layout was `320px 1fr`, a mini calendar
beside a week. MV-2 deleted that component on the 19th and set
`.calendar-layout { display: block }` at the top of the file, so a
grid-template override on a block element overrides nothing. The
wrapper holds nothing live, and removing the opening line plus its one
dead rule leaves the braces balanced - a closing brace would keep a
dead override alive and say it was wanted.

EIGHTY-EIGHT RULES START APPLYING AT DESKTOP WIDTH, which is the whole
risk of this round and the reason it ships with renders at three
widths in three views, before and after. Every one of them was WRITTEN
as a desktop rule - .week-nav-btn's own comment says "the media query
below puts them back to 44" - so this restores intent rather than
changing it. The renders are how that claim is checked rather than
asserted.

Idempotent. Every file backed up to .bak_datebar.
"""
import os
import re
import sys

SUFFIX = '.bak_datebar'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_date_bar.py'
PATCHER = 'apply_date_bar.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'DB-1, 20 Oct 2026'
CHECK = False
CREATES = ()

# THE DEAD WRAPPER, WHOLE. Matched on its own text and on the one rule
# it holds, so this cannot silently eat a different media block if the
# file moves under it.
#
# IT STOPS AT THE CLOSING BRACE OF THE RULE, deliberately. The blank
# line after it carries FOUR TRAILING SPACES, and the first spelling of
# this anchor included them - which the editor writing this file
# silently stripped, so the anchor matched nothing and the round
# refused itself. An anchor must not depend on whitespace nobody can
# see and any tool may remove.
WRAP_WAS = """/* ==================== RESPONSIVE ==================== */
@media screen and (max-width: 1200px) {
    .calendar-layout {
        grid-template-columns: 1fr;
    }
"""
WRAP_NOW = """/* ==================== RESPONSIVE ==================== */
/* THE WRAPPER THAT NEVER CLOSED - DB-1, 20 Oct 2026.
   An `@media screen and (max-width: 1200px) {` opened here, held one
   rule and was never closed, so EVERY rule below it to the end of this
   stylesheet was nested inside it: 88 of them, 2,471 lines, including
   the whole date bar. Above 1200px the arrows rendered as browser
   default buttons - 2px outset black - which is what Demetri reported
   twice.
   IT IS OLD. .bak_mealweek already swallows 722 lines and 54 rules;
   the number has grown with every round that appended CSS since.
   THE ONE RULE INSIDE WAS DEAD TOO: .calendar-layout was `320px 1fr`
   until MV-2 deleted the mini calendar and set `display: block` at the
   top of this file. A grid-template override on a block element
   overrides nothing, so the wrapper is removed rather than closed -
   closing it would keep a dead rule and say somebody wanted it. */
"""


SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-col-body"'; What = 'WC-1: clicking a day opens the picker in WEEK view too - it only did so in Month, because the two views were built in different rounds' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-col-body"'; What = 'WC-1: clicking a day opens the picker in WEEK view too - it only did so in Month, because the two views were built in different rounds' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE WRAPPER THAT NEVER CLOSED'; What = 'DB-1: 88 rules and 2,471 lines were nested inside a max-width 1200px block that was never closed, so the date bar rendered as default browser buttons on any screen wider than that' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },"""

SUITE_WAS = """    'test_picker_stays.py'
)"""
SUITE_NOW = """    'test_picker_stays.py',
    # DB-1, 20 Oct 2026 - the responsive wrapper closes. Section 2
    # asks the BROWSER what media every rule in this file ends up in,
    # which is the question no suite in this system was asking.
    'test_date_bar.py'
)"""

TREE_WAS = """    # PS-1, 19 Oct 2026 - the picker adds on click and stays open,
    # and shows the day so a mis-click can be undone.
    'test_picker_stays.py',
]"""
TREE_NOW = """    # PS-1, 19 Oct 2026 - the picker adds on click and stays open,
    # and shows the day so a mis-click can be undone.
    'test_picker_stays.py',
    # DB-1, 20 Oct 2026 - 88 rules come back out of a media query that
    # was never closed, and a suite starts asking what media a rule is
    # actually in.
    'test_date_bar.py',
]"""

RD_WAS = """    # PS-1, 19 Oct 2026 - the picker adds on click and stays open.
    '.bak_pickerstays',
]"""
RD_NOW = """    # PS-1, 19 Oct 2026 - the picker adds on click and stays open.
    '.bak_pickerstays',
    # DB-1, 20 Oct 2026 - the responsive wrapper that never closed.
    '.bak_datebar',
]"""


# =====================================================================
# A REPAIR THIS ROUND CARRIES - the eight suites of push 2
# =====================================================================
#
# Every one of them ends with:
#
#     ok(_i >= len(alv_rounds.ROUNDS) - 8,
#        'and it is among the eight newest, where this push put it')
#
# which was true while push 2 WAS the newest thing in the register and
# false the moment anything shipped after it. These four rounds ship
# after it. Four of the eight went red; the other four passed by luck,
# sitting one place inside the window, and would go red on the push
# after this one.
#
# IT IS THE SAME MISTAKE THE LINE IT REPLACED WAS MAKING. Push 2
# retired `ROUNDS[-1] == SUFFIX` from eight suites because only one
# round can be last - and put in its place a claim that only EIGHT
# rounds can be in the last eight. A claim about a round's POSITION in
# a list that grows has an expiry date whatever number is written in
# it, so re-pinning to twelve would only move the date.
#
# WHAT IS REAL IS THE DEPENDENCY, and every one of those suites
# already asserts it on the line above: this round sits after the
# rounds whose work it edits, so revert takes them off in the right
# order. That stays true however many rounds ship later.
#
# What replaces the position claim is the other thing that could
# actually be wrong and that nothing was asking: a round registered
# twice. A patcher re-run after its anchor moved would do it.
#
# CARRIED BY DB-1, the OLDEST of the four, on purpose. revert_all.sh
# runs newest first, so a partial revert of this push leaves the
# repair in place; only undoing all four takes it back.
REPAIRS = (
    'test_chip_menu.py', 'test_day_card.py', 'test_month_bar.py',
    'test_picker_stays.py', 'test_planner_back.py',
    'test_recipe_modal.py', 'test_recipe_weight.py',
    'test_week_click.py',
)

CLAIM_WAS = """ok(_i >= len(alv_rounds.ROUNDS) - 8,
   'and it is among the eight newest, where this push put it',
   'it is at %d of %d' % (_i, len(alv_rounds.ROUNDS)))"""
CLAIM_NOW = """# RETIRED - DB-1, 20 Oct 2026. This asked whether the round sat in
# the last eight entries of the register, which was true while push 2
# was the newest thing in it and false as soon as anything shipped
# after it. It is the same mistake as the `ROUNDS[-1] == SUFFIX` it
# replaced: a claim about a POSITION in a growing list expires
# whatever number is in it, so re-pinning would only move the date.
# The dependency claim above is the real one and does not expire.
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once',
   alv_rounds.ROUNDS.count(SUFFIX))"""


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
    raise SystemExit('DB-1 REFUSED: %s' % msg)


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


def style_of(text):
    """The page's own <style> element - the big one, not the includes.

    RD-1's quick-look shell and RD-2's chip menu each ship their own
    <style>, and the browser showed that this matters: the reset that
    flattened the chips is in RD-2's, which is a LATER stylesheet. The
    block this round repairs is the page's own, and it is identified
    by being the largest rather than by being the first.
    """
    best = None
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S):
        if best is None or len(m.group(1)) > len(best.group(1)):
            best = m
    return best


def braces(s):
    """(open, close) counts, comments blanked.

    COUNTED ON CODE, NOT ON TEXT. A brace inside a /* */ is not a
    brace, and this file's comments are full of prose that contains
    them.
    """
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return s.count('{'), s.count('}')


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'THE WRAPPER THAT NEVER CLOSED' in t:
        print('DB-1  already applied - the responsive wrapper is closed.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FAULT MUST BE THERE, AND IT IS A COUNT, NOT A GUESS.
    st = style_of(t.replace('\r\n', '\n'))
    if not st:
        refuse('%s: no <style> element' % TPL)
    op, cl = braces(st.group(1))
    if op != cl + 1:
        refuse('%s: the stylesheet has %d open and %d close brace(s). '
               'This round repairs a file with EXACTLY ONE unclosed '
               'block; anything else is a different fault and wants '
               'looking at by a person.' % (TPL, op, cl))

    t = swap(t, WRAP_WAS, WRAP_NOW, '%s (the dead wrapper)' % TPL)
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

    for rel in REPAIRS:
        pr = os.path.join(root, rel)
        out[pr] = swap(read(pr), CLAIM_WAS, CLAIM_NOW,
                       '%s (the claim that expires)' % rel)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    if not n_was:
        refuse('%s: CONVERTED_N is not readable' % WD)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # DB-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nst = style_of(out[pt].replace('\r\n', '\n'))
    nop, ncl = braces(nst.group(1))
    if nop != ncl:
        refuse('%s: after the edit the stylesheet has %d open and %d '
               'close brace(s) - it must balance' % (TPL, nop, ncl))

    # AND THE MEDIA BLOCKS ARE NOT NESTED ANY MORE. Counted by walking
    # the code, because the whole bug is that a block contained things
    # nobody meant it to.
    code = re.sub(r'/\*.*?\*/', '', nst.group(1), flags=re.S)
    depth, worst = 0, 0
    for m in re.finditer(r'@media[^{]*\{|\{|\}', code):
        tok = m.group(0)
        if tok.startswith('@media'):
            if depth > 0:
                worst = max(worst, depth)
            depth += 1
        elif tok == '{':
            depth += 1
        else:
            depth = max(0, depth - 1)
    if worst > 1:
        refuse('%s: a media query is still nested %d deep inside '
               'another' % (TPL, worst + 1))

    if 'grid-template-columns: 1fr' in T.code_only(out[pt]):
        refuse('%s: the dead .calendar-layout grid override survived'
               % TPL)

    # ALL EIGHT, OR NONE. Four were red and four passed by luck; a
    # repair that fixed only the red ones would leave the same claim
    # to expire on the next push.
    for rel in REPAIRS:
        if 'among the eight newest' in out[os.path.join(root, rel)]:
            refuse('%s: the claim that expires is still there' % rel)
        if 'ROUNDS.count(SUFFIX) == 1' not in \
                out[os.path.join(root, rel)]:
            refuse('%s: nothing replaced it, so the suite now asserts '
                   'one thing less than it did' % rel)

    if CHECK:
        print('DB-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        stylesheet braces %d/%d -> %d/%d'
              % (op, cl, nop, ncl))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('DB-1  applied - the responsive wrapper is gone.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      stylesheet braces %d/%d -> %d/%d' % (op, cl, nop, ncl))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
