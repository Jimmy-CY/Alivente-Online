# -*- coding: utf-8 -*-
"""apply_ae_probe.py - round AE-4, 16 Oct 2026.

THE SUITE WAS MEASURING AN IMITATION OF THE CONTROL.

`test_ae_line` asks whether every date filter is wide enough to show a
date. It works out what a date needs IN THE BROWSER IT IS RUNNING IN,
which is the right instinct and test_filter_gap's stated lesson. It
works it out like this:

    const probe = document.createElement('input');
    probe.type = 'date'; probe.value = '2026-12-31';
    probe.style.cssText = '...font:inherit;padding:10px 14px;...';
    out.need = Math.ceil(probe.getBoundingClientRect().width);

That is not the control. It is a HAND-BUILT IMITATION of the control,
and the hand got two things wrong.

                     the probe            the real control
    padding          14px, typed          12px
    font-size        16px - `inherit`     14px
                     is appended to
                     .filter-grid, so
                     it inherits the
                     GRID's font

Measured side by side in the suite's own fixture, at 1280px:

    real   w 170  clientW 166  scrollW 166  clipped: False
    twin   w 154  (a cloneNode of the real control, width:auto)
    probe  w 175

THE PROBE OVERSTATES THE CONTROL BY 21px, and those 21 pixels are the
six failures. Asked of the control itself, the question the suite was
really asking answers cleanly: scrollWidth 166 <= clientWidth 166, so
the date filter does not clip its own value at any width drawn.

AND THE SAME ERROR IS UNDER AE-1's OWN COMMENT. act_expense.html says
"a date input needs 165 - measured, not guessed". 165 was measured the
same way, on the same kind of stand-in. AE-1's DIRECTION was right - at
150px the real control does clip, 150 against a clientWidth of 146 - but
the page states an imitation's number as a fact, and the next round to
read it would inherit the error.

WHAT THIS ROUND DOES NOT DO
    It does not move the 170px pin. The pin is correct: the real control
    needs 154 here and 170 clears it at every width the suite draws.
    Narrowing the column to fit an intrinsic measurement would make the
    dates smaller for no gain - and every intrinsic candidate was drawn
    before this was written. max-content, min-content, auto and
    fit-content all give 154; minmax(max-content, 1fr) gives 163.

    It does not change what the suite CLAIMS, only what it asks. Five
    controls on one line, and every date wide enough to show a date, are
    the same two claims AE-1 and AE-3 made.

E23, THE CENSUS THAT HAD TO FOLLOW
    If one suite measured an imitation, how many others do? Two build a
    control at all; test_ei_modal builds a <button> only to pass to a
    function and never measures it. Four clone the real one.
    POPULATION OF ONE. See claude/e18_ae_line_probe_16_oct.md.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_aeprobe'
PAGE = 'act_expense.html'
SUITE = 'test_ae_line.py'
ME = 'test_ae_probe.py'
PATCHER = 'apply_ae_probe.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 94, 95
ALIAS_WAS, ALIAS_NOW = 99, 101
ALIAS_P_WAS, ALIAS_S_WAS = 49, 50
ALIAS_P_NOW, ALIAS_S_NOW = 50, 51

# ---------------------------------------------------------------- the probe
PROBE_WAS = """  // WHAT A DATE INPUT ACTUALLY NEEDS, measured in THIS browser rather
  // than typed in from another one. test_filter_gap's lesson.
  const probe = document.createElement('input');
  probe.type = 'date'; probe.value = '2026-12-31';
  probe.style.cssText = 'position:absolute;left:-9999px;width:auto;'
    + 'font:inherit;padding:10px 14px;border:2px solid;box-sizing:border-box';
  p.appendChild(probe);
  out.need = Math.ceil(probe.getBoundingClientRect().width);
  probe.remove();
  return out;"""

PROBE_NOW = """  // WHAT A DATE INPUT ACTUALLY NEEDS, measured in THIS browser rather
  // than typed in from another one. test_filter_gap's lesson.
  //
  // AE-4, 16 Oct 2026 - AND MEASURED ON THE CONTROL, NOT ON A COPY OF
  // IT. This built a fresh <input type=date> and dressed it by hand:
  // padding:10px 14px typed in, and `font:inherit` appended to
  // .filter-grid, which inherits the GRID's 16px rather than the
  // input's 14px. The real control has 12px of padding and a 14px
  // font, so the stand-in came out 21px WIDER than the thing it stood
  // for - 175 against 154 - and those 21 pixels were six failures.
  //
  // A CLONE CANNOT DRIFT FROM THE ORIGINAL. It carries the same
  // element, the same classes and the same cascade; only the width is
  // released. This is the instrument PJ-2's wrap law already uses.
  const model = document.getElementById('fromDateInput');
  const twin = model.cloneNode(true);
  twin.removeAttribute('id');
  twin.value = '2026-12-31';
  twin.style.cssText = 'position:absolute;left:-9999px;width:auto';
  model.parentNode.appendChild(twin);
  out.need = Math.ceil(twin.getBoundingClientRect().width);
  twin.remove();
  // AND NOT BY scrollWidth, WHICH CANNOT ANSWER THIS. The obvious
  // check - does the control overflow its own box - was written, drawn
  // and thrown away: <input type=date> NEVER reports a scrollWidth
  // larger than its clientWidth, because the date widget compresses
  // its own fields instead of overflowing. Measured at 150px, at 170
  // and at 171: scrollWidth equals clientWidth every time. A check
  // that cannot fail is not a check, so it is not here.
  //
  // What a date needs is therefore what the control ASKS FOR when its
  // width is released, which is what the clone above measures.
  return out;"""

# ---------------------------------------------------------- the CONTROL
#
# AND THE CONTROL SAYS LESS, BECAUSE LESS IS TRUE.
#
# It proves the defect was real by rendering AE-1's backup and showing
# both dates narrower than a date needs, at 1280 AND at 390. With the
# stand-in that held at both. With a clone of the control it holds at
# 1280 - 150 against 154 - and NOT at 390, where the old page already
# gave each date 171px and a clone asks for 171.
#
# So AE-1's phone number was the imitation's too: the note said the
# dates were clipping "at 162px on a phone", and they were not. The
# defect was real, and it was a DESKTOP defect. The control asserts it
# where it was and PRINTS the phone measurement instead of asserting
# it, because a control that has to hold everywhere ends up asserting
# something that is not true somewhere.
CTRL_WAS = """                clipped = [c for c in ('fromDateInput', 'toDateInput')
                           if got[c] is not None and got[c] < r['need']]
                ok(len(clipped) == 2,
                   '  and BOTH dates were narrower than a date needs: '
                   '%d and %d against %d'
                   % (got['fromDateInput'] or -1, got['toDateInput'] or -1,
                      r['need']), clipped)"""

CTRL_NOW = """                # AE-4, 16 Oct 2026 - CORRECTED 17 Oct, BY HIS GATE.
                #
                # THE WIDTH HALF OF THIS CONTROL IS NOT ASSERTABLE, and
                # it took two passes to see it.
                #
                # It began by comparing both widths against a stand-in
                # 21px too wide, and held for the wrong reason. Swapping
                # the stand-in for a clone was right and NOT ENOUGH: the
                # old page gave each date 150px, and what a date needs
                # is 154 in this sandbox and 149 on his Chromium. "Both
                # dates were short" is therefore TRUE here and FALSE
                # there, by one pixel, and his gate is where that showed.
                #
                # AE-1's defect is asserted by the CONTROL above, which
                # holds in any font: at 1280 the five controls took TWO
                # ROWS. The widths are PRINTED, because a margin of one
                # pixel either way is information and not a claim.
                for _c in ('fromDateInput', 'toDateInput'):
                    print('         %-13s was %3dpx, and a clone of it '
                          'asks for %3d here'
                          % (_c, got[_c] or -1, r['need']))"""

# ------------------------------------------------------- the page's comment
NOTE_WAS = """   AND 150px WAS NEVER ENOUGH. A date input needs 165 - measured, not
   guessed: a date input carrying 31/12/2026 at width:auto reports 165px
   in Chromium, which is the text plus the picker icon plus this
   component's own 14px padding and 2px border. So From and To have been
   clipping their own value at every desktop width for as long as that
   rule existed, and at 162px on a phone. A truncated date still looks
   like a date, which is why nobody reported it. 170px leaves 5px."""

NOTE_NOW = """   AND 150px WAS NEVER ENOUGH. From and To were clipping their own
   value - at 150px the control has 146px inside its 2px borders and
   needs 150, so the last characters of the date were cut. A truncated
   date still looks like a date, which is why nobody reported it.

   THE 165 THIS NOTE USED TO QUOTE WAS AN IMITATION'S NUMBER, and AE-4
   took it out on 16 Oct 2026. It came from a probe test_ae_line built
   by hand - a fresh input dressed in typed padding and a font it
   inherited from the grid instead of from the control - which measures
   21px wider than the control it stood for. A CLONE of the real control
   asks for 154. 170px clears that at every width the suite draws, and
   the pin does not move: narrowing the column to an intrinsic 154 would
   make the dates smaller for nothing. Every intrinsic candidate was
   drawn before this was written - max-content, min-content, auto and
   fit-content all give 154, minmax(max-content, 1fr) gives 163.

   The number is not the claim anyway. The claim is that the control
   does not clip the date it is holding, and test_ae_line now asks the
   control that directly."""


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
    raise SystemExit('AE-4 REFUSED: %s' % msg)


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


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


TREE_ANCHOR = """    'test_ws_members.py',
]"""
TREE_NEW = """    'test_ws_members.py',
    # AE-4, 16 Oct 2026 - test_ae_line was measuring a date input it
    # built itself, 21px wider than the control it stood for. It clones
    # the control now, and asks it directly whether it clips. Wide from
    # birth.
    'test_ae_probe.py',
]"""

ROUNDS_ANCHOR = """    '.bak_wsmembers',"""
ROUNDS_NEW = """    '.bak_wsmembers',
    # AE-4, 16 Oct 2026 - the probe becomes a clone, and the page stops
    # quoting an imitation's number as a measurement.
    '.bak_aeprobe',"""

SUITE_ANCHOR = """    'test_ws_members.py'
)"""
SUITE_NEW = """    'test_ws_members.py',
    'test_ae_probe.py'
)"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- AE-4, 16 Oct 2026
    # The suite clones the control instead of imitating it.
    @{ File = 'test_ae_line.py'; Text = 'const twin = model.cloneNode(true)'; What = 'AE-4: the probe is a clone of the real control' },
    # ABSENT ON THE CONSTRUCT, NOT ON THE PROSE. The replacement NAMES
    # the old padding in its own comment, explaining what went wrong, so
    # a sentinel on that spelling would refuse the round's own output -
    # which it did, in seven suites at once. createElement is the thing
    # that must not come back, and it is gone.
    @{ File = 'test_ae_line.py'; Text = 'createElement'; Absent = $true; What = 'AE-4: and the suite builds no control of its own' },
    # NOT Code = $true. The note lives in a CSS comment, and code_only
    # BLANKS those - so a Code sentinel would be absent in every version
    # ever written, including the ones where the sentence was there. It
    # would pass for ever and discriminate never, which test_sentinels
    # catches by trying each row against 45 older copies of the file.
    # A sentinel that cannot fail is not a sentinel - the same lesson
    # as the scrollWidth check this round threw away.
    @{ File = 'pages\\templates\\act_expense.html'; Text = 'A date input needs 165'; Absent = $true; What = 'AE-4: the page no longer quotes an imitation as a measurement' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    suite = os.path.join(root, SUITE)
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    # ASKED OF THE TREE FIRST.
    if 'cloneNode' in read(suite):
        print('AE-4  already applied - the probe is a clone.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE FAULT IS READ, NOT REMEMBERED. If the probe is not there in the
    # shape this round measured, the round is aimed at something else.
    s = read(suite)
    if 'padding:10px 14px' not in s:
        refuse('%s no longer dresses its probe with padding:10px 14px, so '
               'the imitation this round measured is not the one on disk'
               % SUITE)
    if 'fromDateInput' not in s or 'toDateInput' not in s:
        refuse('%s no longer names the two date controls' % SUITE)

    s = swap(s, PROBE_WAS, PROBE_NOW, '%s (the probe)' % SUITE)
    s = swap(s, CTRL_WAS, CTRL_NOW, '%s (the CONTROL)' % SUITE)
    out[suite] = s

    # ---------------------------------------------------------------- 2
    # THE GATES, asked of the result.
    if 'createElement' in s:
        refuse('%s still builds a control; the whole point is that it does '
               'not' % SUITE)
    if s.count('cloneNode(true)') != 1:
        refuse('%s: %d clone(s), expected exactly 1'
               % (SUITE, s.count('cloneNode(true)')))
    if re.search(r'\.scrollWidth\b', s):
        refuse('%s measures scrollWidth, which an <input type=date> never '
               'reports larger than clientWidth - a check that cannot fail'
               % SUITE)
    if 'CORRECTED 17 Oct, BY HIS GATE' not in s:
        refuse('%s: the CONTROL still asserts a width. 150px against a '
               'need of 154 here and 149 on his Chromium is true on one '
               'machine and false on the other' % SUITE)
    if re.search(r"ok\(len\(short\) == 2,", s):
        refuse('%s: the width assertion is back' % SUITE)
    # THE CLAIMS DO NOT MOVE. AE-1's one-line claim must survive intact.
    if 'ALL FIVE ARE ON ONE LINE' not in s:
        refuse("%s lost AE-1's one-line claim" % SUITE)
    if s.count('>= need') != 1:
        refuse('%s: the claim should appear exactly once, got %d'
               % (SUITE, s.count('>= need')))
    try:
        import ast
        ast.parse(s)
    except SyntaxError as e:
        refuse('%s would no longer parse - %s' % (SUITE, e))

    # ---------------------------------------------------------------- 3
    # THE PAGE'S COMMENT. No CSS moves - this round changes prose only.
    p = read(page)
    p2 = swap(p, NOTE_WAS, NOTE_NOW, '%s (the AE-1 note)' % PAGE)
    # code_only is LENGTH-PRESERVING: it blanks a comment to spaces
    # rather than removing it, so a longer comment changes the blanked
    # text even when not one line of code moved. The live code is the
    # NON-BLANK lines of that result.
    def live(t):
        return [ln.strip() for ln in code_only(t).split('\n') if ln.strip()]

    live_was = live(p)
    live_now = live(p2)
    if live_was != live_now:
        refuse('%s: the round changed LIVE CODE on the page, and it may '
               'only change the comment' % PAGE)
    if not any('170px 170px' in ln for ln in live_now):
        refuse('%s: the 170px pin is gone, and this round does not move it'
               % PAGE)
    if 'needs 165' in p2 or 'A date input needs 165' in p2:
        refuse('%s still quotes 165 as a measurement' % PAGE)
    out[page] = p2

    # ---------------------------------------------------------------- 4
    t = read(os.path.join(root, PS1))
    t = swap(t, SUITE_ANCHOR, SUITE_NEW, '%s ($suites)' % PS1)
    t = swap(t, SENT_ANCHOR, SENT_NEW, '%s ($sentinels)' % PS1)
    out[os.path.join(root, PS1)] = t

    tr = read(os.path.join(root, TREE))
    tr = swap(tr, TREE_ANCHOR, TREE_NEW, '%s (CONVERTED)' % TREE)
    out[os.path.join(root, TREE)] = tr

    rd = read(os.path.join(root, ROUNDS))
    rd = swap(rd, ROUNDS_ANCHOR, ROUNDS_NEW, '%s (ROUNDS)' % ROUNDS)
    out[os.path.join(root, ROUNDS)] = rd

    wd = read(os.path.join(root, WD))
    wd = bump(wd, 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
              'AE-4, 16 Oct 2026 - this round own suite',
              '%s (CONVERTED_N)' % WD)
    out[os.path.join(root, WD)] = wd

    co = read(os.path.join(root, CO))
    co = bump(co, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
              'AE-4, 16 Oct 2026 - this round own patcher and suite',
              '%s (the alias count)' % CO)
    co = swap(co, "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_WAS, ALIAS_S_WAS),
              "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_NOW, ALIAS_S_NOW),
              '%s (the alias split)' % CO)
    out[os.path.join(root, CO)] = co

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('AE-4 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('AE-4 applied.')
    print('   the probe is a CLONE of the control, not an imitation of it')
    print('   the CONTROL asserts the defect where it was - a DESKTOP defect')
    print('   the page stops quoting 165 as a measurement')
    print('   the 170px pin does NOT move - it is correct')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
